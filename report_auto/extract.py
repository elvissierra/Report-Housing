"""
Read Data
I/O helpers for reading raw tabular data.

This module centralizes header normalization (lower_snake_case), whitespace trimming,
and empty-string → nan conversion so downstream transforms can assume consistent inputs.
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from report_auto.utils import clean_list_string, normalize_headers


def load_csv(path: str) -> pd.DataFrame:
    """
    Read a CSV and normalize headers/cell whitespace; return a clean DataFrame.
    """
    df = pd.read_csv(path)
    df = normalize_headers(df)

    # Treat blank strings as missing values (nan) for reliable numeric and boolean ops
    df = df.replace(r"^\s*$", np.nan, regex=True)
    # Trim whitespace from all string cells without touching non-strings
    df = df.map(clean_list_string)
    return df
