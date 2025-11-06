"""
Data Prepping - Standardize
Utility helpers for string normalization and token handling used across the pipeline.
Keep these decoupled so they can be reused in tests and notebooks.
"""

from __future__ import annotations
from typing import Iterable, Dict, List, Tuple, Optional
import pandas as pd
import math
import re


def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Copy with columns normalized to lower_snake_case
    """
    out = df.copy()
    out.columns = out.columns.str.strip().str.lower().str.replace(" ", "_")
    return out


def normalize_name(s: object) -> str:
    """
    Normalize a name to lower_snake_case and strip dedupe suffix like '.1'
    useful when mapping config names to DF columns
    """
    val = str(s or "").strip().lower()
    val = re.sub(r"\s+", "_", val)
    val = re.sub(r"\.(?:\d+)$", "", val)
    return val


def normalize_delim(raw) -> Optional[str]:
    """
    Whitespace delimiters are valid; only nan/"" == None.
    """
    if pd.isna(raw):
        return None
    s = str(raw)
    return None if s == "" else s


def ensure_series(obj: pd.Series | pd.DataFrame) -> pd.Series:
    """
    Use first column if DataFrame; else return the series.
    """
    return obj.iloc[:, 0] if isinstance(obj, pd.DataFrame) else obj


def make_unique_columns(cols: Iterable[object]) -> List[str]:
    """
    Append .1, .2, ... to duplicates; first occurrence stays unsuffixed.
    """
    seen: Dict[str, int] = {}
    out: List[str] = []
    for c in cols:
        name = str(c)
        idx = seen.get(name, 0)
        new_name = name if idx == 0 else f"{name}.{idx}"
        seen[name] = idx + 1
        out.append(new_name)
    return out


def deduplicate_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
    """
    Return (df_with_unique_names, base_to_group_map).
    """
    if not df.columns.duplicated().any():
        return df, {}
    out = df.copy()
    original = list(out.columns)
    seen: Dict[str, int] = {}
    groups: Dict[str, List[str]] = {}
    new_cols: List[str] = []
    for name in original:
        base = str(name)
        idx = seen.get(base, 0)
        new_name = base if idx == 0 else f"{base}.{idx}"
        seen[base] = idx + 1
        new_cols.append(new_name)
        groups.setdefault(base, []).append(new_name)
    out.columns = new_cols
    return out, groups


def sort_dupe_items_key(item: Tuple[object, int]) -> Tuple[int, str]:
    """
    (value, count) → sort by count desc, then value asc.
    """
    value, cnt = item
    return (-int(cnt), str(value))


def sort_label_items_key(item: Tuple[str, int]) -> Tuple[int, str]:
    """
    (label, count) → sort by count desc, then label asc.
    """
    label, cnt = item
    return (-int(cnt), str(label))


def compute_percentages(counts: Dict[str, int]) -> Dict[str, int]:
    """
    Turn counts into integer %
    Tie-break: bigger fractional part first, then label asc for determinism.
    """
    total = int(sum(counts.values()))
    if total <= 0:
        return {k: 0 for k in counts}
    raw = {k: 100.0 * v / total for k, v in counts.items()}
    floors = {k: int(math.floor(p)) for k, p in raw.items()}
    remainder = 100 - sum(floors.values())
    fracs = {k: (raw[k] - floors[k]) for k in counts}
    order = sorted(counts.keys(), key=lambda k: (-fracs[k], str(k)))
    for i in range(remainder):
        floors[order[i % len(order)]] += 1
    return floors


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


def parse_exclude_keys(raw: object) -> set[str]:
    """
    Parse a pipe-separated string into a normalized set (lowercased, stripped).
    """
    if raw is None:
        return set()
    try:
        if pd.isna(raw):
            return set()
    except Exception:
        pass
    s = str(raw).strip()
    if not s:
        return set()
    return {token.strip().lower() for token in s.split("|") if token.strip()}
