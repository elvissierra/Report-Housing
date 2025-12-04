import logging
import pandas as pd
import schemas
from .helpers import prepare_data_groups, format_group_name

logger = logging.getLogger(__name__)


def run(df: pd.DataFrame, step: schemas.TimeSeriesAnalysis) -> schemas.ReportBlock:
    """
    Performs a time series analysis and returns a structured ReportBlock.

    Output layout:
    - Single group:  Timestamp | Value
    - Multiple groups: Group | Timestamp | Value
    """
    all_series_dfs: list[pd.DataFrame] = []

    metric_to_agg = "mean" if step.metric == "average" else step.metric

    try:
        data_groups = prepare_data_groups(df, step)
    except ValueError as e:
        logger.error(
            "Error preparing data groups for step '%s': %s",
            step.output_name,
            e,
            exc_info=True,
        )
        error_df = pd.DataFrame(
            [
                {
                    "Group": "N/A",
                    "Timestamp": "N/A",
                    "Value": f"Data preparation failed: {e}",
                }
            ]
        )
        return schemas.ReportBlock(
            title=f"Error in step: {step.output_name}", data=error_df
        )

    for group_name, group_df in data_groups:
        if group_df.empty:
            logger.info(
                "Group '%s' is empty after initial filtering. Skipping time series.",
                format_group_name(group_name),
            )
            continue

        formatted_group_name = format_group_name(group_name)
        working_df = group_df.copy()

        # Check required columns
        missing_cols: list[str] = []
        if step.date_column not in working_df.columns:
            missing_cols.append(step.date_column)
        if step.metric_column not in working_df.columns:
            missing_cols.append(step.metric_column)

        if missing_cols:
            error_message = (
                "Missing required columns for time series: " + ", ".join(missing_cols)
            )
            logger.warning("Group '%s': %s", formatted_group_name, error_message)
            error_df = pd.DataFrame(
                [
                    {
                        "Group": formatted_group_name,
                        "Timestamp": "N/A",
                        "Value": error_message,
                    }
                ]
            )
            all_series_dfs.append(error_df)
            continue

        try:
            # Convert types robustly
            working_df[step.date_column] = pd.to_datetime(
                working_df[step.date_column], errors="coerce"
            )
            working_df[step.metric_column] = pd.to_numeric(
                working_df[step.metric_column], errors="coerce"
            )

            # Drop rows where date or metric conversion failed
            working_df.dropna(
                subset=[step.date_column, step.metric_column], inplace=True
            )

            if working_df.empty:
                error_message = (
                    "No valid data after date/metric conversion and dropping NaNs."
                )
                logger.info(
                    "Group '%s': %s", formatted_group_name, error_message
                )
                error_df = pd.DataFrame(
                    [
                        {
                            "Group": formatted_group_name,
                            "Timestamp": "N/A",
                            "Value": error_message,
                        }
                    ]
                )
                all_series_dfs.append(error_df)
                continue

            # Resample and aggregate
            time_series_result = (
                working_df.set_index(step.date_column)
                .resample(step.frequency)[step.metric_column]
                .agg(metric_to_agg)
            )

            # Fill NaNs only for sum / count; drop for averages
            if step.metric in ["sum", "count"]:
                time_series_result = time_series_result.fillna(0)
            time_series_result = time_series_result.dropna()

            if time_series_result.empty:
                error_message = (
                    "Time series result is empty after resampling and aggregation."
                )
                logger.info(
                    "Group '%s': %s", formatted_group_name, error_message
                )
                error_df = pd.DataFrame(
                    [
                        {
                            "Group": formatted_group_name,
                            "Timestamp": "N/A",
                            "Value": error_message,
                        }
                    ]
                )
                all_series_dfs.append(error_df)
                continue

            # Convert to DataFrame with explicit Timestamp / Value columns
            result_df = time_series_result.reset_index()
            result_df = result_df.rename(
                columns={step.date_column: "Timestamp", step.metric_column: "Value"}
            )
            result_df["Group"] = formatted_group_name

            all_series_dfs.append(result_df)

        except Exception as e:
            logger.error(
                "Error in Time Series Analysis for group '%s': %s",
                formatted_group_name,
                e,
                exc_info=True,
            )
            error_df = pd.DataFrame(
                [
                    {
                        "Group": formatted_group_name,
                        "Timestamp": "N/A",
                        "Value": f"Analysis failed: {e}",
                    }
                ]
            )
            all_series_dfs.append(error_df)
            continue

    # Final assembly & layout normalization
    if not all_series_dfs:
        logger.info("No time series results generated for step '%s'.", step.output_name)
        final_df = pd.DataFrame(columns=["Column", "Timestamp", "Value"])
    else:
        raw_df = pd.concat(all_series_dfs, ignore_index=True)

        # The time series is always for a single metric_column per step; we treat
        # that metric as the "Column" label for consistency with other advanced
        # analyses.
        metric_label = step.metric_column

        # Drop dataset-level group if present; for now we focus on the metric itself.
        if "Group" in raw_df.columns:
            raw_df = raw_df.drop(columns=["Group"])

        # Ensure Timestamp/Value exist even for error cases.
        for col in ("Timestamp", "Value"):
            if col not in raw_df.columns:
                raw_df[col] = pd.NA

        raw_df = raw_df[["Timestamp", "Value"]]

        try:
            if pd.api.types.is_datetime64_any_dtype(raw_df["Timestamp"]):
                raw_df["Timestamp"] = raw_df["Timestamp"].dt.date
        except Exception:
            pass

        pretty_rows: list[dict] = []

        # One header row followed by all data points.
        pretty_rows.append(
            {
                "Column": metric_label,
                "Timestamp": "",
                "Value": "",
            }
        )
        for _, r in raw_df.iterrows():
            pretty_rows.append(
                {
                    "Column": "",
                    "Timestamp": r["Timestamp"],
                    "Value": r["Value"],
                }
            )

        final_df = pd.DataFrame(pretty_rows)

    return schemas.ReportBlock(title=step.output_name, data=final_df)