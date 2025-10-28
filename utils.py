import pandas as pd
import re

# Data Prepping - Standardize

def safe_lower(val):
    return str(val).strip().lower() if pd.notna(val) else ""


def split_values(value, delimiter: str) -> list:
    if pd.isna(value) or not isinstance(value, (str, int, float)):
        return []
    if not delimiter:
        return []
    try:
        return [v.strip() for v in str(value).split(delimiter) if v.strip()]
    except Exception:
        return []


def get_root_value(value: str, delimiter: str) -> str:
    return split_values(value, delimiter)[0] if split_values(value, delimiter) else ""


def clean_string(value: str) -> str:
    return str(value).strip() if isinstance(value, str) else value


def clean_list_string(val):
    if pd.isna(val):
        return ""
    s = str(val)
    # Keep letters, digits, spaces, commas, and common symbols often present in data
    s = re.sub(r"[^a-zA-Z0-9,%_\-/() ]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()
