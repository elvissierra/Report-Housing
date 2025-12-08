import math
from typing import Dict

import numpy as np
import pandas as pd

import schemas
from .helpers import prepare_data_groups, format_group_name, apply_transformations


def run(df: pd.DataFrame, step: schemas.CustomAnalysis) -> schemas.ReportBlock:
    """
    Orchestrates the custom analysis pipeline and returns a structured ReportBlock.

    For each CustomAnalysis step:

    - We apply filters/grouping via helpers.prepare_data_groups.
    - For each target column in each group, we run the selected operation
      (average, distribution, duplicate_count, list_unique_values).
    - We attach Group/Column context **only** when needed
      (grouped or multi-column analyses).

    The resulting DataFrame is intentionally "payload only" for the common
    single-column, full-dataset case so the streamer can format it into the
    3-column layout used by Report_Housing.
    """
    all_results_dfs = []
    op = step.operation

    multi_context = bool(step.group_by) or len(step.target_columns) > 1

    include_group_fields = multi_context and op in ("average", "sum", "median")

    # Dispatcher for helper functions
    op_handlers = {
        "average": _op_average,
        "sum": _op_sum,
        "median": _op_median,
        "distribution": _op_distribution,
        "duplicate_count": _op_duplicate_count,
        "list_unique_values": _op_list_unique_values,
    }

    handler = op_handlers.get(op)
    if not handler:
        # Unknown operation → return a small error block
        error_df = pd.DataFrame([{"Error": f"Unknown custom operation: '{op}'"}])
        return schemas.ReportBlock(
            title=f"Error in step: {step.output_name}", data=error_df
        )

    data_groups = prepare_data_groups(df, step)
    group_fields = step.group_by or []

    for group_name, group_df in data_groups:
        # Decode the pandas groupby key into a mapping of group-by column -> value
        group_context: Dict[str, object] = {}
        if group_fields:
            if isinstance(group_name, tuple):
                raw_values = list(group_name)
            else:
                raw_values = [group_name]

            # Pad or truncate to match the number of group-by fields
            if len(raw_values) < len(group_fields):
                raw_values += [None] * (len(group_fields) - len(raw_values))
            elif len(raw_values) > len(group_fields):
                raw_values = raw_values[: len(group_fields)]

            group_context = dict(zip(group_fields, raw_values))

        if group_df.empty:
            continue

        formatted_group_name = format_group_name(group_name)

        for col_name in step.target_columns:
            if col_name not in group_df.columns:
                # This specific column is missing from the group
                error_df = pd.DataFrame(
                    [
                        {
                            "Group": formatted_group_name,
                            "Column": col_name,
                            "Error": "Column not found",
                        }
                    ]
                )
                all_results_dfs.append(error_df)
                continue

            # Base series and transformations
            series = group_df[col_name]
            transformed_series = apply_transformations(
                series, step.transformations, step.post_transformation_filters
            )

            result_df = handler(transformed_series)

            if multi_context:
                result_df["Group"] = formatted_group_name
                result_df["Column"] = col_name

                if include_group_fields:
                    for field_name, field_value in group_context.items():
                        result_df[field_name] = field_value

            all_results_dfs.append(result_df)

    # Assemble final DataFrame
    if not all_results_dfs:
        final_df = pd.DataFrame([{"Message": "No data produced for this analysis"}])
    else:
        final_df = pd.concat(all_results_dfs, ignore_index=True)

        if (
            include_group_fields
            and group_fields
            and len(step.target_columns) == 1
            and op in ("average", "sum", "median")
            and {"Group", "Column"}.issubset(final_df.columns)
        ):
            exclude = set(["Group", "Column"] + list(group_fields))
            metric_cols = [c for c in final_df.columns if c not in exclude]

            if metric_cols:
                target_label = step.target_columns[0]
                metric_label_map = {
                    "average": "Average of",
                    "sum": "Sum of",
                    "median": "Median of",
                }
                prefix = metric_label_map.get(op, "Value for")
                new_metric_name = f"{prefix} {target_label}"
                final_df = final_df.rename(columns={metric_cols[0]: new_metric_name})
                metric_cols[0] = new_metric_name

            # Keep group-by columns first, followed by the metric column(s).
            ordered_cols = list(group_fields) + metric_cols
            final_df = final_df[ordered_cols]

        elif (
            multi_context
            and op == "distribution"
            and {"Group", "Column"}.issubset(final_df.columns)
        ):
            # Ensure stable column order for distribution tables
            value_col = ""
            core_cols = [value_col, "%", "Count"]
            pretty_rows: list[dict] = []

            for (grp, col), sub in final_df.groupby(["Group", "Column"], sort=False):
                # Section header row
                pretty_rows.append(
                    {
                        "Group": grp,
                        "Column": col,
                        value_col: "",
                        "%": "",
                        "Count": "",
                    }
                )
                # Detail rows: one per distinct value
                for _, r in sub.iterrows():
                    pretty_rows.append(
                        {
                            "Group": "",
                            "Column": "",
                            value_col: r.get(value_col, ""),
                            "%": r.get("%", ""),
                            "Count": r.get("Count", ""),
                        }
                    )

            final_df = pd.DataFrame(
                pretty_rows, columns=["Group", "Column"] + core_cols
            )

        elif (
            multi_context
            and op == "duplicate_count"
            and {"Group", "Column"}.issubset(final_df.columns)
        ):
            pretty_rows = []

            for (grp, col), sub in final_df.groupby(["Group", "Column"], sort=False):
                # Section header row
                pretty_rows.append(
                    {
                        "Group": grp,
                        "Column": col,
                        "Duplicates": "",
                        "Instances": "",
                    }
                )
                # Detail rows: one per duplicated value
                for _, r in sub.iterrows():
                    pretty_rows.append(
                        {
                            "Group": "",
                            "Column": "",
                            "Duplicates": r.get("Duplicates", ""),
                            "Instances": r.get("Instances", ""),
                        }
                    )

            final_df = pd.DataFrame(
                pretty_rows, columns=["Group", "Column", "Duplicates", "Instances"]
            )

        else:
            # Reorder columns to have context first only when we actually added them.
            if multi_context and {"Group", "Column"}.issubset(final_df.columns):
                # Keep the generic Group/Column context first. For aggregation
                # operations we then include explicit group-by fields, followed by
                # the metric payload columns (Average, Sum, etc.).
                context_cols = ["Group", "Column"]
                if include_group_fields:
                    context_cols += list(group_fields)
                # Deduplicate in case a group field name happens to be "Group" or "Column"
                seen = set()
                ordered_context_cols = []
                for c in context_cols:
                    if c not in seen and c in final_df.columns:
                        ordered_context_cols.append(c)
                        seen.add(c)

                data_cols = [
                    c for c in final_df.columns if c not in ordered_context_cols
                ]
                final_df = final_df[ordered_context_cols + data_cols]

    return schemas.ReportBlock(title=step.output_name, data=final_df)


# --- HELPER FUNCTIONS ---


def _compute_percentages(counts: pd.Series) -> pd.Series:
    """
    Turn counts into integer percentages that sum to 100.

    This mirrors Report_Housing's compute_percentages logic:
    - Compute raw percentages.
    - Take floors.
    - Distribute remaining points to the largest fractional parts.
    """
    total = int(counts.sum())
    if total <= 0:
        return pd.Series([0] * len(counts), index=counts.index)

    raw = (counts.astype(float) * 100.0) / float(total)
    floors = raw.apply(math.floor)
    remainder = int(100 - floors.sum())

    fracs = raw - floors
    order = list(fracs.sort_values(ascending=False).index)

    i = 0
    while remainder > 0 and order:
        key = order[i % len(order)]
        floors.loc[key] += 1
        remainder -= 1
        i += 1

    return floors.astype(int)


def _op_average(series: pd.Series) -> pd.DataFrame:
    """
    Calculates the average and returns a one-column DataFrame.

    Layout (Report_Housing style):
    - Single column named 'Average'
    - Single row with the mean of the series (rounded to 2 decimals)
    """
    numeric_series = pd.to_numeric(series, errors="coerce").dropna()
    if numeric_series.empty:
        return pd.DataFrame({"Average": [np.nan]})
    mean_val = float(round(numeric_series.mean(), 2))
    return pd.DataFrame({"Average": [mean_val]})


def _op_sum(series: pd.Series) -> pd.DataFrame:
    """
    Calculates the sum and returns a one-column DataFrame.

    Layout (Report_Housing style):
    - Single column named 'Sum'
    - Single row with the sum of the series (rounded to 2 decimals)
    """
    numeric_series = pd.to_numeric(series, errors="coerce").dropna()
    if numeric_series.empty:
        return pd.DataFrame({"Sum": [np.nan]})
    sum_val = float(round(numeric_series.sum(), 2))
    return pd.DataFrame({"Sum": [sum_val]})


def _op_median(series: pd.Series) -> pd.DataFrame:
    s = series.dropna()
    if s.empty:
        return pd.DataFrame({"Median": [np.nan]})

    # 1) Try numeric median
    numeric_series = pd.to_numeric(s, errors="coerce").dropna()
    if not numeric_series.empty:
        median_val = float(round(numeric_series.median(), 2))
        return pd.DataFrame({"Median": [median_val]})

    # 2) Fallback: try datetime median
    dt_series = pd.to_datetime(s, errors="coerce").dropna()
    if not dt_series.empty:
        median_dt = dt_series.median()
        # If you want MM/DD/YYYY format, change this line:
        median_str = median_dt.strftime("%m/%d/%Y")
        return pd.DataFrame({"Median": [median_str]})

    return pd.DataFrame({"Median": [np.nan]})


def _op_duplicate_count(series: pd.Series) -> pd.DataFrame:
    """
    Identifies duplicated values and returns a structured table.

    Layout (Report_Housing style):
    - Columns: 'Duplicates', 'Instances'
    - One row per value that appears more than once in the series.
    """
    # Normalize to string for counting
    s = series.dropna().astype(str)
    if s.empty:
        return pd.DataFrame(columns=["Duplicates", "Instances"])

    counts = s.value_counts()
    dupes = counts[counts > 1]

    if dupes.empty:
        return pd.DataFrame(columns=["Duplicates", "Instances"])

    df = dupes.reset_index()
    df.columns = ["Duplicates", "Instances"]
    df["Instances"] = df["Instances"].astype(int)
    return df


def _op_distribution(series: pd.Series) -> pd.DataFrame:
    """
    Calculates value distribution and returns a structured DataFrame.

    Layout (Report_Housing style for categorical columns):
    - First column: the distinct values (header is '')
    - Second column: '%' (integer percentage string with '%')
    - Third column: 'Count'
    """
    s = series.dropna()
    if s.empty:
        return pd.DataFrame(columns=["", "%", "Count"])

    counts = s.value_counts()
    percentages = _compute_percentages(counts)

    values = counts.index.astype(str)
    pct_values = percentages.reindex(counts.index).astype(int)

    dist_df = pd.DataFrame(
        {
            "": values,
            "%": pct_values.astype(str) + "%",
            "Count": counts.values,
        }
    )

    return dist_df


def _op_list_unique_values(series: pd.Series) -> pd.DataFrame:
    """
    Gets unique values and returns a single-column DataFrame.

    This is mostly for debugging / inspection; the streamer will treat it
    as a generic simple block and still limit to 3 columns in the final CSV.
    """
    s = series.dropna()
    if s.empty:
        return pd.DataFrame(columns=["Unique Value"])

    unique_values = s.unique()
    try:
        # Try sorting numerically if possible
        sorted_values = np.sort(unique_values)
    except TypeError:
        # Fallback to string sorting for mixed types
        sorted_values = np.sort(unique_values.astype(str))

    return pd.DataFrame(sorted_values, columns=["Unique Value"])
