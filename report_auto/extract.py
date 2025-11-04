"""
I/O helpers for reading raw tabular data.

This module centralizes header normalization (lower_snake_case), whitespace trimming,
and empty-string → NaN conversion so downstream transforms can assume consistent inputs.
"""

from __future__ import annotations
import pandas as pd
import numpy as np

# Read Data


def load_csv(path: str) -> pd.DataFrame:
    """Read a CSV and normalize headers/cell whitespace; return a clean DataFrame."""
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Treat blank strings as missing values (NaN) for reliable numeric and boolean ops
    df = df.replace(r"^\s*$", np.nan, regex=True)
    # Trim whitespace from all string cells without touching non-strings
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    return df
