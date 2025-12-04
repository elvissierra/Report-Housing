import re
# backend/app/extract.py
import pandas as pd
from typing import IO, Any

# Define specific pandas errors to catch
from pandas.errors import ParserError, EmptyDataError

CUSTOM_NA_VALUES = [
    '',        # Empty string
    '#N/A',    # Excel's Not Available
    '#N/A N/A',
    '#NA',
    '-1.#IND',
    '-1.#QNAN',
    '-NaN',
    '-nan',
    '1.#IND',
    '1.#QNAN',
    '<NA>',    # Pandas' own missing value indicator
    'N/A',     # Not Applicable
    'NULL',    # SQL NULL
    'NaN',     # The string 'NaN'
    'n/a',
    'nan',
    'null',
    '?',       # Common placeholder for missing
    'None'     # Python's None
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
    """
    Internal helper to normalize column names to a canonical lower_snake_case form.
    """
    df = df.copy()
    df.columns = [_normalize_column_name(col) for col in df.columns]
    return df


def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Internal helper to apply standard, non-destructive cleaning to a DataFrame.
    """
    df = _normalize_headers(df)

    # Correctly trim whitespace ONLY from object/string columns without destroying other types.
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].str.strip()

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


            df = pd.read_csv(file_object, sep=None, engine='python', on_bad_lines='warn', keep_default_na=False, na_values=CUSTOM_NA_VALUES)

        elif filename_lower.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_object, na_values=CUSTOM_NA_VALUES)
        else:
            # Raise a specific, informative error.
            raise TypeError("Unsupported file type. Please upload a CSV or Excel file.")
    
    
    # --- Correct, Specific Error Handling ---
    except (ParserError, EmptyDataError) as e:
        # Catch specific pandas errors and provide a user-friendly message.
        raise ValueError(f"Failed to parse the file. It may be malformed or empty. Details: {e}")
    except Exception as e:
        # A fallback for truly unexpected errors (e.g., file read errors).
        raise IOError(f"Could not read the file '{filename}'. Error: {e}")

    if df.empty:
        raise ValueError("The uploaded file is empty or contains no data.")
    return _clean_dataframe(df.copy())
