import pandas as pd
import schemas
from .helpers import prepare_data_groups, format_group_name, apply_transformations


ALLOWED_TRANSFORMATIONS = {"split_and_explode", "strip_whitespace"}


def run(df: pd.DataFrame, step: schemas.CrosstabAnalysis) -> schemas.ReportBlock:
    """
    Generates a cross-tabulation analysis, correctly handling transformations and reshaping.
    """
    all_crosstab_dfs = []

    if step.column_transformations:
        for col_trans in step.column_transformations:
            for trans in col_trans.transformations:
                if trans.action not in ALLOWED_TRANSFORMATIONS:
                    raise ValueError(
                        f"Transformation '{trans.action}' is not supported by Crosstab Analysis."
                    )

    data_groups = prepare_data_groups(df, step)

    for group_name, group_df in data_groups:
        if group_df.empty:
            continue

        working_df = (
            group_df[[step.index_column, step.column_to_compare]].copy().dropna()
        )

        if step.column_transformations:
            for col_trans in step.column_transformations:
                if col_trans.column_name in working_df.columns:
                    working_df[col_trans.column_name] = apply_transformations(
                        working_df[col_trans.column_name], col_trans.transformations, []
                    )

        working_df = (
            working_df.explode(step.index_column)
            .explode(step.column_to_compare)
            .dropna()
        )

        if working_df.empty:
            continue

        crosstab_result = pd.crosstab(
            working_df[step.index_column],
            working_df[step.column_to_compare],
            margins=True,
        )

        if step.show_percentages == "index":
            crosstab_result = crosstab_result.div(crosstab_result["All"], axis=0)
        elif step.show_percentages == "columns":
            crosstab_result = crosstab_result.div(crosstab_result.loc["All"], axis=1)
        elif step.show_percentages == "all":
            grand_total = crosstab_result.loc["All", "All"]
            if grand_total > 0:
                crosstab_result = crosstab_result / grand_total

        crosstab_result = crosstab_result.reset_index()
        crosstab_result["Group"] = format_group_name(group_name)
        all_crosstab_dfs.append(crosstab_result)

    if not all_crosstab_dfs:
        final_df = pd.DataFrame(columns=["Group", "Data"])
    else:
        final_df = pd.concat(all_crosstab_dfs, ignore_index=True)
        cols = ["Group"] + [col for col in final_df.columns if col != "Group"]
        final_df = final_df[cols]

    return schemas.ReportBlock(title=step.output_name, data=final_df)
