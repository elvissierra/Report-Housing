import pandas as pd


def to_csv_string(df: pd.DataFrame, header: bool = False) -> str:
    """
    Converts a DataFrame to a CSV formatted string.
    The output has no index. The header is optional.
    """
    return df.to_csv(index=False, header=header)
