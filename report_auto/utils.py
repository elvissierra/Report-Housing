"""
Data Prepping - Standardize
Utility helpers for string normalization and token handling used across the pipeline.
Keep these decoupled so they can be reused in tests and notebooks.
"""

from __future__ import annotations
import pandas as pd
import re


# NOTE: Currently unused in the main pipeline (kept for potential reuse).
def safe_lower(val: object) -> str:
    """
    Lowercase a value safely; None/NaN → empty string to simplify downstream comparisons.
    """
    return str(val).strip().lower() if pd.notna(val) else ""


# NOTE: Currently unused in the main pipeline (kept for potential reuse).
def split_values(value: object, delimiter: str) -> list[str]:
    """
    Split a scalar by a delimiter into trimmed parts; robust to NaNs and non-strings.
    """
    if pd.isna(value) or not isinstance(value, (str, int, float)):
        return []
    if not delimiter:
        return []
    try:
        return [v.strip() for v in str(value).split(delimiter) if v.strip()]
    except Exception:
        return []


# NOTE: Currently unused in the main pipeline (kept for potential reuse).
def get_root_value(value: object, delimiter: str) -> str:
    """
    Return the first token from `split_values`, or empty string when unavailable.
    """
    return split_values(value, delimiter)[0] if split_values(value, delimiter) else ""


# NOTE: Currently unused in the main pipeline (kept for potential reuse).
def clean_string(value: object) -> object:
    """
    Trim surrounding whitespace for strings; pass non-strings through unchanged.
    """
    return str(value).strip() if isinstance(value, str) else value


def clean_list_string(val: object) -> str:
    """
    Sanitize list-like display strings by allowing only letters, digits,
    spaces, and commas. Remove all other punctuation (e.g., underscores,
    slashes, percent signs, parentheses). Normalize comma spacing and
    collapse repeated spaces.
    """
    if pd.isna(val):
        return ""
    s = str(val)
    # Keep letters, digits, spaces, and commas only and drop everything else
    s = re.sub(r"[^a-zA-Z0-9, ]+", " ", s)
    # Normalize commas so to ensure a single space after commas and no leading/trailing commas
    s = re.sub(r"\s*,\s*", ", ", s)  # unify comma spacing
    s = re.sub(r"(,\s*)+", ", ", s)  # collapse repeated commas
    # Collapse repeated whitespace
    s = re.sub(r"\s+", " ", s)
    return s.strip(" ,")
