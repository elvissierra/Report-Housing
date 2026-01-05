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
        # Not all file-like objects are seekable; ignore if not.
        pass


def _read_sample_text(file_object: IO[Any], size: int = 65536) -> str:
    """Read a small sample without consuming the stream for subsequent reads."""
    _seek_start(file_object)
    sample = file_object.read(size)
    _seek_start(file_object)

    # UploadFile.file is often bytes; normalize to str for csv.Sniffer.
    if isinstance(sample, bytes):
        return sample.decode("utf-8-sig", errors="replace")
    return str(sample)


def _detect_delimiter(sample_text: str) -> str:
    """Detect a likely delimiter for common tabular exports."""
    delimiters = [",", "\t", ";", "|"]

    # Prefer Sniffer when possible.
    try:
        dialect = csv.Sniffer().sniff(sample_text, delimiters=delimiters)
        if getattr(dialect, "delimiter", None) in delimiters:
            return dialect.delimiter
    except Exception:
        pass

    # Fallback: choose the delimiter that appears most often in the header line.
    header_line = sample_text.splitlines()[0] if sample_text else ""
    counts = {d: header_line.count(d) for d in delimiters}
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else ","


def _read_csv_robust(file_object: IO[Any]) -> pd.DataFrame:
    """Read CSV with robust delimiter detection and safer failure modes."""
    sample_text = _read_sample_text(file_object)
    delimiter = _detect_delimiter(sample_text)

    _seek_start(file_object)
    df = pd.read_csv(
        file_object,
        sep=delimiter,
        engine="python",
        on_bad_lines="warn",
        keep_default_na=False,
        na_values=CUSTOM_NA_VALUES,
    )

    # Sanity check: if we detected a delimiter but only got 1 column, this is
    # very likely a delimiter/quoting issue that will cascade into "Column not found".
    if df.shape[1] == 1:
        header_line = sample_text.splitlines()[0] if sample_text else ""
        if any(d in header_line for d in [",", "\t", ";", "|"]):
            raise ValueError(
                "Detected only 1 column when reading the CSV. "
                "This usually means the delimiter was mis-detected or the file contains unescaped delimiters/quotes. "
                f"Detected delimiter: {repr(delimiter)}. "
                "Please re-export the CSV with proper quoting or confirm the delimiter."
            )

    return df


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
            df = _read_csv_robust(file_object)

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
