import logging
from typing import List

import pandas as pd
import schemas
from .helpers import prepare_data_groups, format_group_name, apply_transformations

logger = logging.getLogger(__name__)

ALLOWED_TRANSFORMATIONS = {
    "to_numeric",
    "fill_na",
    "split_and_explode",
    "strip_whitespace",
}


def _validate_transformations(
    column_transformations: List[schemas.ColumnTransformation],
) -> None:
    """
    Ensure only supported transformations are used for summary statistics.
    """
    for trans_detail in column_transformations or []:
        for trans in trans_detail.transformations:
            if trans.action not in ALLOWED_TRANSFORMATIONS:
                raise ValueError(
                    f"Transformation '{trans.action}' is not supported by Summary Statistics."
                )


def run(df: pd.DataFrame, step: schemas.SummaryStatsAnalysis) -> schemas.ReportBlock:
    """
    Runs a summary statistics analysis, correctly handling row-changing transformations
    (like split and explode) at the column level, and returning a clean, rule-style
    output layout.

    Output layout:
    - Single group + single numeric column: Metric | Value
    - Multiple groups or multiple columns: Group | Column | Metric | Value
    """
    all_stats_dfs: list[pd.DataFrame] = []

    # --- Validate transformations before starting ---
    _validate_transformations(step.column_transformations)

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
                    "Column": "N/A",
                    "Metric": "Error",
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
                "Group '%s' is empty after filtering. Skipping summary stats.",
                format_group_name(group_name),
            )
            continue

        formatted_group_name = format_group_name(group_name)

        for col_name in step.numeric_columns:
            if col_name not in group_df.columns:
                logger.warning(
                    "Column '%s' not found in group '%s'. Skipping for summary stats.",
                    col_name,
                    formatted_group_name,
                )
                error_df = pd.DataFrame(
                    [
                        {
                            "Group": formatted_group_name,
                            "Column": col_name,
                            "Metric": "Error",
                            "Value": "Column not found",
                        }
                    ]
                )
                all_stats_dfs.append(error_df)
                continue

            try:
                series_to_transform = group_df[col_name].copy()

                col_trans_details = next(
                    (
                        ct
                        for ct in (step.column_transformations or [])
                        if ct.column_name == col_name
                    ),
                    None,
                )

                transformed_series = series_to_transform
                has_split_and_explode = False

                if col_trans_details:
                    transformed_series = apply_transformations(
                        series_to_transform,
                        col_trans_details.transformations,
                        [],
                    )
                    has_split_and_explode = any(
                        t.action == "split_and_explode"
                        for t in col_trans_details.transformations
                    )

                # Handle explode if requested
                series_for_stats = transformed_series
                if has_split_and_explode:
                    series_for_stats = series_for_stats.explode().dropna()

                # Coerce to numeric and compute stats
                numeric_series = pd.to_numeric(
                    series_for_stats, errors="coerce"
                ).dropna()

                if numeric_series.empty:
                    logger.info(
                        "Numeric series for column '%s' in group '%s' is empty after "
                        "transformations/coercion. Skipping.",
                        col_name,
                        formatted_group_name,
                    )
                    error_df = pd.DataFrame(
                        [
                            {
                                "Group": formatted_group_name,
                                "Column": col_name,
                                "Metric": "Error",
                                "Value": "No numeric data for analysis",
                            }
                        ]
                    )
                    all_stats_dfs.append(error_df)
                    continue

                stats_series = numeric_series.describe()

                if "count" in stats_series.index:
                    stats_series["count"] = int(stats_series["count"])
                stats_series = stats_series.round(2)

                stats_df = (
                    stats_series.to_frame(name="Value")
                    .reset_index()
                    .rename(columns={"index": "Metric"})
                )
                stats_df["Group"] = formatted_group_name
                stats_df["Column"] = col_name

                # Insert a context row so the table clearly states which column these stats belong to.
                context_row = pd.DataFrame(
                    [
                        {
                            "Group": formatted_group_name,
                            "Column": col_name,
                            "Metric": "Column",
                            "Value": col_name,
                        }
                    ]
                )

                stats_df = pd.concat([context_row, stats_df], ignore_index=True)

                all_stats_dfs.append(stats_df)

            except Exception as e:
                logger.error(
                    "Error processing column '%s' in group '%s' for summary stats: %s",
                    col_name,
                    formatted_group_name,
                    e,
                    exc_info=True,
                )
                error_df = pd.DataFrame(
                    [
                        {
                            "Group": formatted_group_name,
                            "Column": col_name,
                            "Metric": "Error",
                            "Value": f"Analysis failed: {e}",
                        }
                    ]
                )
                all_stats_dfs.append(error_df)
                continue

    # Final assembly & layout normalization
    if not all_stats_dfs:
        logger.info("No summary statistics generated for step '%s'.", step.output_name)
        final_df = pd.DataFrame(columns=["Column", "Metric", "Value"])
    else:
        raw_df = pd.concat(all_stats_dfs, ignore_index=True)

        if "Group" in raw_df.columns:
            raw_df = raw_df.drop(columns=["Group"])

        for col in ("Column", "Metric", "Value"):
            if col not in raw_df.columns:
                raw_df[col] = pd.NA

        raw_df = raw_df[["Column", "Metric", "Value"]]

        pretty_rows: list[dict] = []
        for col_name, sub in raw_df.groupby("Column", sort=False):
            # Header row for this numeric column
            pretty_rows.append(
                {
                    "Column": col_name,
                    "Metric": "",
                    "Value": "",
                }
            )
            # Detail rows: each metric/value pair with a blank Column cell
            for _, r in sub.iterrows():
                pretty_rows.append(
                    {
                        "Column": "",
                        "Metric": r["Metric"],
                        "Value": r["Value"],
                    }
                )

        final_df = pd.DataFrame(pretty_rows)

    return schemas.ReportBlock(title=step.output_name, data=final_df)
