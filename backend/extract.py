import re
import csv

import pandas as pd
from typing import IO, Any

# Define specific pandas errors to catch
from pandas.errors import ParserError, EmptyDataError

CUSTOM_NA_VALUES = [
    "",  # Empty string
    "#N/A",  # Excel's Not Available
    "#N/A N/A",
    "#NA",
    "-1.#IND",
    "-1.#QNAN",
    "-NaN",
    "-nan",
    "1.#IND",
    "1.#QNAN",
    "<NA>",  # Pandas' own missing value indicator
    "N/A",  # Not Applicable
    "NULL",  # SQL NULL
    "NaN",  # The string 'NaN'
    "n/a",
    "nan",
    "null",
    "?",  # Common placeholder for missing
    "None",  # Python's None
]

def _seek_start(file_object: IO[Any]) -> None:
    """Best-effort rewind for file-like objects used by pandas."""
    try:
        file_object.seek(0)
    except Exception:
        pass


def _read_sample_text(file_object: IO[Any], size: int = 256_000) -> str:
    """Read a small sample without consuming the stream for subsequent reads."""
    _seek_start(file_object)
    sample = file_object.read(size)
    _seek_start(file_object)

    if isinstance(sample, bytes):
        return sample.decode("utf-8-sig", errors="replace")
    return str(sample)


def _find_unbalanced_quote_lines(sample_text: str, max_hits: int = 12) -> list[int]:
    """Heuristic: find lines with an odd number of unescaped quote chars.

    Removes doubled quotes ("") which represent a literal quote in CSV.
    This helps identify malformed exports with stray/unclosed quotes.
    """
    hits: list[int] = []
    for idx, line in enumerate(sample_text.splitlines(), start=1):
        stripped = line.replace('""', "")
        if stripped.count('"') % 2 == 1:
            hits.append(idx)
            if len(hits) >= max_hits:
                break
    return hits


def _normalize_column_name(name: str) -> str:
    """
    Normalizes a single column header to a canonical form:
    - strip leading/trailing whitespace
    - collapse internal whitespace
    - lowercase
    - replace non-alphanumeric characters with underscores
    - collapse multiple underscores and trim them from the ends
    """
    name = str(name).strip()
    name = re.sub(r"\s+", " ", name)
    name = name.lower()
    name = re.sub(r"[^\w]+", "_", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")
    return name


def _normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names to canonical lower_snake_case AND make them unique.

    Why: If a DataFrame has duplicate column names, df['col'] returns a DataFrame,
    which breaks code expecting Series methods like .str.strip().
    """
    df = df.copy()

    normalized = [_normalize_column_name(col) for col in df.columns]

    seen: dict[str, int] = {}
    unique_cols: list[str] = []
    for name in normalized:
        base = name or "column"
        count = seen.get(base, 0) + 1
        seen[base] = count
        unique_cols.append(base if count == 1 else f"{base}_{count}")

    df.columns = unique_cols
    return df


def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Internal helper to apply standard, non-destructive cleaning to a DataFrame.
    """
    df = _normalize_headers(df)

    # Correctly trim whitespace ONLY from object/string columns without destroying other types.
    for col in df.select_dtypes(include=["object"]).columns:
        value = df[col]
        if isinstance(value, pd.DataFrame):
            df[col] = value.apply(lambda s: s.str.strip())
        else:
            df[col] = value.str.strip()

    return df


def load_tabular_data(file_object: IO[Any], filename: str) -> pd.DataFrame:
    """
    Reads tabular data (CSV or Excel) from a file-like object, cleans it,
    and returns a standardized pandas DataFrame. This is the application's "Strong Border".
    """
    filename_lower = filename.lower()

    try:
        if filename_lower.endswith(".csv"):
            # Let pandas infer dtypes, don't force everything to string.
            # In extract.py, inside load_tabular_data, right before pd.read_csv/excel

            df = pd.read_csv(
                file_object,
                sep=None,
                engine="python",
                on_bad_lines="error",
                keep_default_na=False,
                na_values=CUSTOM_NA_VALUES,
            )

        elif filename_lower.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_object, na_values=CUSTOM_NA_VALUES)
        else:
            # Raise a specific, informative error.
            raise TypeError("Unsupported file type. Please upload a CSV or Excel file.")

    # --- Correct, Specific Error Handling ---
    except (ParserError, EmptyDataError) as e:
        sample_text = _read_sample_text(file_object)
        bad_quote_lines = _find_unbalanced_quote_lines(sample_text)
    
        if bad_quote_lines:
            raise ValueError(
                "Failed to parse the CSV due to malformed quoting (unbalanced \"). "
                "This typically happens when a field contains a raw quote that wasn't escaped "
                '(CSV uses doubled quotes: ""). '
                f"Check these line numbers in the uploaded file (1-based, sample scan): {bad_quote_lines}. "
                f"Details: {e}"
            )
    
        raise ValueError(
            f"Failed to parse the file. It may be malformed or empty. Details: {e}"
        )
    except Exception as e:
        # A fallback for truly unexpected errors (e.g., file read errors).
        raise IOError(f"Could not read the file '{filename}'. Error: {e}")

    if df.empty:
        raise ValueError("The uploaded file is empty or contains no data.")
    return _clean_dataframe(df.copy())
