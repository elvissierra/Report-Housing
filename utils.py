from __future__ import annotations

"""
Utility helpers for string normalization and token handling used across the pipeline.
Keep these side-effect free so they can be reused in tests and notebooks.
"""

import pandas as pd
import re

# Data Prepping - Standardize


def safe_lower(val: object) -> str:
    """Lowercase a value safely; None/NaN → empty string to simplify downstream comparisons."""
    return str(val).strip().lower() if pd.notna(val) else ""


def split_values(value: object, delimiter: str) -> list[str]:
    """Split a scalar by a delimiter into trimmed parts; robust to NaNs and non-strings."""
    if pd.isna(value) or not isinstance(value, (str, int, float)):
        return []
    if not delimiter:
        return []
    try:
        return [v.strip() for v in str(value).split(delimiter) if v.strip()]
    except Exception:
        return []


def get_root_value(value: object, delimiter: str) -> str:
    """Return the first token from `split_values`, or empty string when unavailable."""
    return split_values(value, delimiter)[0] if split_values(value, delimiter) else ""


def clean_string(value: object) -> object:
    """Trim surrounding whitespace for strings; pass non-strings through unchanged."""
    return str(value).strip() if isinstance(value, str) else value


def clean_list_string(val: object) -> str:
    """
    Sanitize list-like display strings by removing exotic characters while
    keeping common symbols (%, _ , - , /, parentheses). Collapse repeated spaces.
    """
    if pd.isna(val):
        return ""
    s = str(val)
    # Keep letters, digits, spaces, commas, and common symbols often present in data
    s = re.sub(r"[^a-zA-Z0-9,%_\-/() ]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()
