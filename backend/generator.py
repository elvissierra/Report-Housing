import pandas as pd

# Characters that spreadsheet applications (Excel, Google Sheets, LibreOffice Calc)
# interpret as formula prefixes, enabling CSV injection.
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _sanitize_cell(value: object) -> object:
    """
    Prefix string values that start with a formula character with a single-quote
    so spreadsheets render them as plain text instead of executing them as formulas.
    """
    if isinstance(value, str) and value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value


def _sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of *df* with all string cells sanitized against CSV injection."""
    sanitized = df.copy()
    for col in sanitized.select_dtypes(include="object").columns:
        sanitized[col] = sanitized[col].map(_sanitize_cell)
    return sanitized


def to_csv_string(df: pd.DataFrame, header: bool = False) -> str:
    """
    Converts a DataFrame to a CSV formatted string.
    The output has no index. The header is optional.
    String values starting with formula-prefix characters are escaped so they
    cannot be executed as spreadsheet formulas (CSV injection prevention).
    """
    return _sanitize_dataframe(df).to_csv(index=False, header=header)
