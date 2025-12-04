import pandas as pd
import numpy as np
import schemas
from .helpers import prepare_data_groups, format_group_name

def run(df: pd.DataFrame, step: schemas.OutlierDetectionAnalysis) -> schemas.ReportBlock:
    """
    Identifies outliers and returns a structured ReportBlock of the findings.

    Behaviour:
    - Coerces target columns to numeric (so numeric-looking strings are handled).
    - Emits explicit rows when there is no numeric data or when no outliers
      are detected for a given column.
    """
    outlier_records = []

    data_groups = prepare_data_groups(df, step)

    for group_name, group_df in data_groups:
        if group_df.empty:
            continue

        formatted_group_name = format_group_name(group_name)

        for col_name in step.target_columns:
            if col_name not in group_df.columns:
                outlier_records.append(
                    {
                        "Group": formatted_group_name,
                        "Original Row Index": pd.NA,
                        "Column": col_name,
                        "Outlier Value": "Column not found",
                        "Method": step.method.upper(),
                    }
                )
                continue

            raw_series = group_df[col_name]
            # Coerce to numeric so we can handle numeric-looking strings
            series = pd.to_numeric(raw_series, errors="coerce").dropna()

            if series.empty:
                outlier_records.append(
                    {
                        "Group": formatted_group_name,
                        "Original Row Index": pd.NA,
                        "Column": col_name,
                        "Outlier Value": "No numeric data for analysis",
                        "Method": step.method.upper(),
                    }
                )
                continue

            lower_bound, upper_bound = -np.inf, np.inf

            if step.method == "iqr":
                Q1, Q3 = series.quantile(0.25), series.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - (step.threshold * IQR)
                upper_bound = Q3 + (step.threshold * IQR)
            elif step.method == "z-score":
                mean, std_dev = series.mean(), series.std()
                lower_bound = mean - (step.threshold * std_dev)
                upper_bound = mean + (step.threshold * std_dev)

            outliers = series[(series < lower_bound) | (series > upper_bound)]

            if outliers.empty:
                outlier_records.append(
                    {
                        "Group": formatted_group_name,
                        "Original Row Index": pd.NA,
                        "Column": col_name,
                        "Outlier Value": "No outliers detected",
                        "Method": step.method.upper(),
                    }
                )
                continue

            for index, value in outliers.items():
                outlier_records.append(
                    {
                        "Group": formatted_group_name,
                        "Original Row Index": index,
                        "Column": col_name,
                        "Outlier Value": value,
                        "Method": step.method.upper(),
                    }
                )

        if not outlier_records:
            final_df = pd.DataFrame(
                columns=["Column", "Original Row Index", "Outlier Value", "Method"]
            )
        else:
            raw_df = pd.DataFrame(outlier_records)

            if "Group" in raw_df.columns:
                raw_df = raw_df.drop(columns=["Group"])

            raw_df = raw_df[["Column", "Original Row Index", "Outlier Value", "Method"]]

            pretty_rows: list[dict] = []
            for col_name, sub in raw_df.groupby("Column", sort=False):

                pretty_rows.append(
                    {
                        "Column": col_name,
                        "Original Row Index": pd.NA,
                        "Outlier Value": pd.NA,
                        "Method": "",
                    }
                )

                for _, r in sub.iterrows():
                    pretty_rows.append(
                        {
                            "Column": "",
                            "Original Row Index": r["Original Row Index"],
                            "Outlier Value": r["Outlier Value"],
                            "Method": r["Method"],
                        }
                    )

            final_df = pd.DataFrame(pretty_rows)

        return schemas.ReportBlock(title=step.output_name, data=final_df)