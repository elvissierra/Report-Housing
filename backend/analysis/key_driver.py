import pandas as pd
import numpy as np
import statsmodels.api as sm
import schemas
from .helpers import prepare_data_groups, format_group_name


def run(df: pd.DataFrame, step: schemas.KeyDriverAnalysis) -> schemas.ReportBlock:
    """
    Performs a multiple linear regression, correctly handling categorical features
    and other model parameters defined in the schema.

    The output layout is:
    - Single group:  Feature | Coefficient | Standard Error | P-value
    - Multiple groups: Group | Feature | Coefficient | Standard Error | P-value
    """
    all_results_dfs = []

    data_groups = prepare_data_groups(df, step)

    for group_name, group_df in data_groups:
        if group_df.empty:
            continue

        formatted_group_name = format_group_name(group_name)

        # 1. Data preparation
        all_cols = [step.target_variable] + step.feature_columns
        working_df = group_df[all_cols].copy().dropna(subset=all_cols)

        # Separate numeric and categorical features based on the schema
        categorical_features = step.categorical_features or []
        numeric_features = [
            f for f in step.feature_columns if f not in categorical_features
        ]

        # One-hot encode the specified categorical features
        if categorical_features:
            dummies = pd.get_dummies(
                working_df[categorical_features],
                drop_first=True,
                dtype=float,
            )
            working_df = pd.concat(
                [working_df[numeric_features + [step.target_variable]], dummies],
                axis=1,
            )
            final_feature_columns = numeric_features + list(dummies.columns)
        else:
            final_feature_columns = numeric_features

        # Convert all remaining columns to numeric, coercing errors
        for col in [step.target_variable] + final_feature_columns:
            if col in working_df.columns:
                working_df[col] = pd.to_numeric(working_df[col], errors="coerce")

        working_df.dropna(inplace=True)

        # Need at least (features + 1) rows to estimate the model
        if len(working_df) <= len(final_feature_columns) + 1:
            continue

        Y = working_df[step.target_variable]
        X = working_df[final_feature_columns]

        # Honor the include_intercept flag
        if step.include_intercept:
            X = sm.add_constant(X)

        try:
            model = sm.OLS(Y, X).fit()
            results_summary = model.summary2()
            coeffs_df = results_summary.tables[1]

            p_col = "P>|t|"
            if p_col not in coeffs_df.columns:
                # Unexpected layout; skip this group
                continue

            significant_rows_mask = coeffs_df[p_col] < step.p_value_threshold

            if step.include_intercept and "const" in coeffs_df.index:
                # Always keep intercept if it exists
                significant_rows_mask.loc["const"] = True

            coeffs_df = coeffs_df[significant_rows_mask]

            # Rename columns to a clean, stable schema
            coeffs_df = coeffs_df.rename(
                columns={
                    "Coef.": "Coefficient",
                    "Std.Err.": "Standard Error",
                    p_col: "P-value",
                }
            )

            result_df = (
                coeffs_df[["Coefficient", "Standard Error", "P-value"]]
                .reset_index()
                .rename(columns={"index": "Feature"})
            )
            result_df["Group"] = formatted_group_name

            # Round numeric fields to 2 decimal places for presentation
            for col in ("Coefficient", "Standard Error", "P-value"):
                if col in result_df.columns:
                    result_df[col] = result_df[col].round(2)

            # Add an R-squared row for this group (also rounded)
            r_squared_df = pd.DataFrame(
                [
                    {
                        "Feature": "R-squared",
                        "Coefficient": round(model.rsquared, 2),
                        "Standard Error": np.nan,
                        "P-value": np.nan,
                        "Group": formatted_group_name,
                    }
                ]
            )

            final_group_df = pd.concat([result_df, r_squared_df], ignore_index=True)
            all_results_dfs.append(final_group_df)

        except Exception:
            # If this group's regression fails, skip it but keep other groups
            continue

    # Final assembly & layout normalization
    if not all_results_dfs:
        final_df = pd.DataFrame(
            columns=["Feature", "Coefficient", "Standard Error", "P-value"]
        )
    else:
        final_df = pd.concat(all_results_dfs, ignore_index=True)

        multi_group = "Group" in final_df.columns and final_df["Group"].nunique() > 1

        if multi_group:
            final_df = final_df[
                ["Group", "Feature", "Coefficient", "Standard Error", "P-value"]
            ]
        else:
            final_df = final_df[["Feature", "Coefficient", "Standard Error", "P-value"]]

    return schemas.ReportBlock(title=step.output_name, data=final_df)
