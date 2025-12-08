import pandas as pd
import numpy as np
import itertools
import schemas
from .helpers import prepare_data_groups, format_group_name, cramers_v, is_categorical


# Helper to compute correlation ratio (eta) for categorical–numeric pairs
def correlation_ratio(categories: pd.Series, values: pd.Series) -> float:
    """
    Computes the correlation ratio (eta) between a categorical and numeric series.

    Eta measures how much of the variance in the numeric variable is explained
    by differences between the category means (0 = no relationship, 1 = perfect).
    """
    df = pd.DataFrame(
        {"cat": categories, "val": pd.to_numeric(values, errors="coerce")}
    ).dropna()
    if df.empty:
        return float("nan")

    overall_mean = df["val"].mean()
    if np.isnan(overall_mean):
        return float("nan")

    groups = df.groupby("cat")["val"]
    ss_between = 0.0
    for _, g in groups:
        if g.empty:
            continue
        n_g = float(len(g))
        mean_g = g.mean()
        ss_between += n_g * (mean_g - overall_mean) ** 2

    ss_total = float(((df["val"] - overall_mean) ** 2).sum())
    if ss_total <= 0.0:
        return float("nan")

    eta = np.sqrt(ss_between / ss_total)
    return float(eta)


def run(df: pd.DataFrame, step: schemas.CorrelationAnalysis) -> schemas.ReportBlock:
    """Calculates statistical correlations and returns a structured ReportBlock."""
    correlation_records = []

    data_groups = prepare_data_groups(df, step)
    for group_name, group_df in data_groups:
        if group_df.empty:
            continue

        formatted_group_name = format_group_name(group_name)
        column_pairs = list(itertools.combinations(step.columns, 2))

        for col1_name, col2_name in column_pairs:
            if col1_name not in group_df.columns or col2_name not in group_df.columns:
                continue

            col1, col2 = group_df[col1_name].dropna(), group_df[col2_name].dropna()
            aligned_col1, aligned_col2 = col1.align(col2, join="inner")

            if aligned_col1.empty:
                continue

            is_col1_cat = is_categorical(aligned_col1)
            is_col2_cat = is_categorical(aligned_col2)

            if not is_col1_cat and not is_col2_cat:
                # Numeric–numeric: Pearson
                corr_type, corr_val = "Pearson", aligned_col1.corr(aligned_col2)
            elif is_col1_cat and is_col2_cat:
                # Categorical–categorical: Cramér's V
                corr_type, corr_val = (
                    "Cramér's V",
                    cramers_v(aligned_col1, aligned_col2),
                )
            else:
                # Mixed types (one categorical, one numeric): use correlation ratio (eta)
                if is_col1_cat and not is_col2_cat:
                    cat, num = aligned_col1, aligned_col2
                elif is_col2_cat and not is_col1_cat:
                    cat, num = aligned_col2, aligned_col1
                else:
                    # If we somehow can't classify, skip this pair
                    continue
                corr_type, corr_val = (
                    "Correlation ratio (eta)",
                    correlation_ratio(cat, num),
                )

            if pd.isna(corr_val) or abs(corr_val) < step.threshold:
                continue

            correlation_records.append(
                {
                    "Group": formatted_group_name,
                    "Column 1": col1_name,
                    "Column 2": col2_name,
                    "Correlation Type": corr_type,
                    "Correlation Value": corr_val,
                }
            )

    if not correlation_records:
        final_df = pd.DataFrame(
            columns=[
                "Group",
                "Column 1",
                "Column 2",
                "Correlation Type",
                "Correlation Value",
            ]
        )
    else:
        final_df = pd.DataFrame(correlation_records)

    return schemas.ReportBlock(title=step.output_name, data=final_df)
