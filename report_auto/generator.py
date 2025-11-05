"""
Report Assembly
"""

import pandas as pd


def assemble_report(sections: list[list[str | int]]) -> pd.DataFrame:
    """
    Flatten a list of 3-column blocks into one DataFrame, inserting a blank spacer row
    between blocks so the final CSV renders as visually separated sections.
    """
    final_rows = []
    for block in sections:
        final_rows.extend(block + [["", "", ""]])
    return pd.DataFrame(final_rows)


def save_report(df: pd.DataFrame, output_path: str) -> None:
    """
    Persist the assembled report to CSV without headers or index; print a success badge
    """
    df.to_csv(output_path, index=False, header=False)
    print(f"✅ Report saved to {output_path}")
