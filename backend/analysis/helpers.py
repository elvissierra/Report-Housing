# backend/app/analysis/helpers.py
import pandas as pd
import schemas

# from __future__ import annotations
from typing import List
from scipy.stats import chi2_contingency
import numpy as np


def prepare_data_groups(df: pd.DataFrame, step: schemas.BaseAnalysis) -> list:
    """
    Applies filters and then groups the data. Enforces the correct order of operations.
    Returns an iterable of (group_name, group_dataframe).
    """
    filtered_df = df.copy()
    if step.filters:
        for f in step.filters:
            col = filtered_df[f.column]

            # Defensive guard: Filter.column should resolve to a Series, not a DataFrame.
            if isinstance(col, pd.DataFrame):
                raise TypeError(
                    f"Filter column '{f.column}' resolved to a DataFrame; expected a Series. "
                    "Check your filter configuration."
                )

            if f.operator == "eq":
                filtered_df = filtered_df[col == f.value]
            elif f.operator == "neq":
                filtered_df = filtered_df[col != f.value]
            elif f.operator == "gt":
                filtered_df = filtered_df[col > f.value]
            elif f.operator == "lt":
                filtered_df = filtered_df[col < f.value]
            elif f.operator == "in":
                filtered_df = filtered_df[col.isin(f.value)]
            elif f.operator == "not_in":
                filtered_df = filtered_df[~col.isin(f.value)]
            elif f.operator == "contains":
                filtered_df = filtered_df[col.astype(str).str.contains(f.value, na=False)]

    if step.group_by:
        return filtered_df.groupby(step.group_by, dropna=False)
    else:
        return [("Full Dataset", filtered_df)]


def format_group_name(group_name) -> str:
    """
    Formats the group name from a pandas groupby object into a clean string.
    """
    if isinstance(group_name, tuple):
        return ", ".join(map(str, group_name))
    return str(group_name)


def apply_transformations(
    series: pd.Series,
    transformations: List[schemas.Transformation],
    post_filters: List[schemas.Filter],
) -> pd.Series:
    """
    Applies a series of transformations and then post-transformation filters to a Series.
    """
    if not isinstance(series, pd.Series):
        raise TypeError(f"apply_transformations expects a pandas Series, got {type(series)}")

    s = series.copy()

    for trans in transformations:
        action, params = trans.action, trans.params
        if action == "split_and_explode":
            delimiter = params.get("delimiter")
            if not delimiter:
                raise ValueError("split_and_explode requires a 'delimiter' in params.")
            # Split into lists, then explode so each value is counted independently.
            s = s.astype(str).str.split(delimiter).explode()
        elif action == "to_root_node":
            delimiter = params.get("delimiter")
            if not delimiter:
                raise ValueError("to_root_node requires a 'delimiter' in params.")
            s = s.astype(str).str.split(delimiter).str[0]
        elif action == "strip_whitespace":
            s = s.astype(str).str.strip()
        elif action == "to_numeric":
            s = pd.to_numeric(s, errors="coerce")
        elif action == "fill_na":
            s = s.fillna(params.get("value", 0))

    if post_filters:
        for f in post_filters:
            if f.operator == "eq":
                s = s[s == f.value]
            elif f.operator == "neq":
                s = s[s != f.value]
            elif f.operator == "gt":
                s = s[pd.to_numeric(s, errors="coerce") > f.value]
            elif f.operator == "lt":
                s = s[pd.to_numeric(s, errors="coerce") < f.value]
            elif f.operator == "in":
                s = s[s.isin(f.value)]
            elif f.operator == "not_in":
                s = s[~s.isin(f.value)]
            elif f.operator == "contains":
                s = s[s.astype(str).str.contains(f.value, na=False)]

    return s


# This helper will require front end support. The application will "suggest" if a column is categorical or numeric, but won't decide outright without user input. (
# Example why this matters: Col A is a collumn showing stars for moving ratings. 1, 2, 3, 4, 5 are actually categorical despite looking numerical, as 1 is equivalent to very bad while 5 is very good
def is_categorical(series: pd.Series) -> bool:
    """
    Determines if a Series is categorical based on its actual data type.
    """
    # This is the most reliable way to check for string-like data.
    return pd.api.types.is_string_dtype(series)


def cramers_v(x: pd.Series, y: pd.Series) -> float:
    """
    Calculates Cramér's V statistic for categorical-categorical association.
    This is a pure, self-contained statistical function.
    """
    # --- Create a contingency table (crosstab) of the two series.
    confusion_matrix = pd.crosstab(x, y)

    # --- Chi-squared test: This tests whether the observed distribution of
    # frequencies differs from the expected distribution.
    # chi2, _, _, _ = chi2_contingency(confusion_matrix)
    chi2, _, _, _ = chi2_contingency(confusion_matrix, correction=False)

    # --- Calculate Cramér's V from the Chi-squared value.
    # It normalizes Chi-squared from 0 (no association) to 1 (perfect association).
    n = confusion_matrix.sum().sum()
    if n == 0:
        return 0.0
    phi2 = chi2 / n
    r, k = confusion_matrix.shape

    # --- The formula for Cramér's V.
    # It adjusts for the number of rows and columns in the contingency table.
    v = np.sqrt(phi2 / min(k - 1, r - 1))
    return v
