import pandas as pd
import numpy as np
import itertools
import schemas
from .helpers import prepare_data_groups, format_group_name, cramers_v, is_categorical


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
                corr_type, corr_val = "Pearson", aligned_col1.corr(aligned_col2)
                if not (pd.isna(corr_val) or abs(corr_val) < step.threshold):
                    correlation_records.append(
                        {
                            "Group": formatted_group_name,
                            "Column 1": col1_name,
                            "Column 2": col2_name,
                            "Correlation Type": corr_type,
                            "Correlation Value": corr_val,
                        }
                    )
            elif is_col1_cat and is_col2_cat:
                corr_type, corr_val = (
                    "Cramér's V",
                    cramers_v(aligned_col1, aligned_col2),
                )
                if not (pd.isna(corr_val) or abs(corr_val) < step.threshold):
                    correlation_records.append(
                        {
                            "Group": formatted_group_name,
                            "Column 1": col1_name,
                            "Column 2": col2_name,
                            "Correlation Type": corr_type,
                            "Correlation Value": corr_val,
                        }
                    )
            else:
                # Mixed types (one numeric, one categorical) are not summarized by a single
                # correlation coefficient in this table. We skip these pairs here and let
                # the Crosstab analyses handle them instead.
                continue

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
