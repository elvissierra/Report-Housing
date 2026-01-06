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
    """Normalize column names to canonical lower_snake_case and make them unique.

    Why: If a DataFrame has duplicate column names, `df["col"]` returns a DataFrame
    (not a Series). Downstream string ops like `.str.strip()` then fail.

    We de-duplicate by appending a numeric suffix: col, col_2, col_3, ...
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
    # If duplicate column names exist, df[col] returns a DataFrame; handle that safely.
    for col in df.select_dtypes(include=["object"]).columns:
        value = df[col]
        if isinstance(value, pd.DataFrame):
            # Multiple columns share the same name; trim each sub-column.
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
                # Keep CSV quoting enabled (default). Disabling quoting (QUOTE_NONE)
                # often *creates* "Expected N fields, saw M" when delimiters exist
                # inside quoted text fields.
                sep=None,
                engine="python",
                on_bad_lines="warn",
                keep_default_na=False,
                na_values=CUSTOM_NA_VALUES,
                quotechar='"',
                doublequote=True,
            )

        elif filename_lower.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_object, na_values=CUSTOM_NA_VALUES)
        else:
            # Raise a specific, informative error.
            raise TypeError("Unsupported file type. Please upload a CSV or Excel file.")

    # --- Correct, Specific Error Handling ---
    except (ParserError, EmptyDataError) as e:
        # Catch specific pandas errors and provide a user-friendly message.
        raise ValueError(
            f"Failed to parse the file. It may be malformed or empty. Details: {e}"
        )
    except Exception as e:
        # A fallback for truly unexpected errors (e.g., file read errors).
        raise IOError(f"Could not read the file '{filename}'. Error: {e}")

    if df.empty:
        raise ValueError("The uploaded file is empty or contains no data.")
    return _clean_dataframe(df.copy())
