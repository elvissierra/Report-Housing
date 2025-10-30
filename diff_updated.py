
"""
 Stand alone script to compare columns in what was present and what is now present between strings.
 e.g. String original: "F 1541 Merivale Rd , …" String compared against: "D 1541 Ch Merivale , …"
"""

import re
import pandas as pd
import argparse
from pathlib import Path

# This pattern extracts four logical fields from a free-form audit string:
# - 'existing'  : everything after the literal 'existing ' up to ', proposed'
# - 'proposed'  : everything after 'proposed ' up to ', index'
# - 'index'     : the integer value following 'index '
# - 'is_meaningful' : the literal tail 'is meaningful true|false'
# The non-greedy '.*?' ensures we stop at the next sentinel even if commas exist inside values.
PATTERN = re.compile(
    r"""
    existing\s+(?P<existing>.*?)(?=,\s*proposed\b)   # keep flag if present
    ,\s*proposed\s+(?P<proposed>.*?)(?=,\s*index\b)  # keep flag if present
    ,\s*index\s+(?P<index>\d+)\s*,\s*
    (?P<is_meaningful>is\s+meaningful\s+(?:true|false))
    """,
    re.IGNORECASE | re.VERBOSE,
)

def extract_parts(text: str):
    """Return a Series(existing, proposed, index, is_meaningful_str) parsed from one cell."""
    cols = ["existing", "proposed", "index", "is_meaningful_str"]
    if not isinstance(text, str):
        return pd.Series([None, None, None, None], index=cols)
    m = PATTERN.search(text)
    if not m:
        return pd.Series([None, None, None, None], index=cols)
    gd = m.groupdict()
    return pd.Series(
        [
            gd["existing"].strip(),         # e.g., "F 1541 Merivale Rd , …"
            gd["proposed"].strip(),         # e.g., "D 1541 Ch Merivale , …"
            int(gd["index"]),
            gd["is_meaningful"].strip(),    # literal tail, e.g., "is meaningful true"
        ],
        index=cols,
    )

def split_diff_updated(df: pd.DataFrame) -> pd.DataFrame:
    """Vectorize `extract_parts` over the 'diff_updated' column and join back to the DataFrame."""
    parts = df["diff_updated"].apply(extract_parts)
    return pd.concat([df, parts], axis=1)

# --- CLI runner ---

def main():
    """CLI wrapper: read input CSV, parse 'diff_updated', and write four clean columns."""
    parser = argparse.ArgumentParser(
        description=(
            "Parse the 'diff_updated' column from a CSV and emit four columns: "
            "existing, proposed, index, is_meaningful_str."
        )
    )
    parser.add_argument(
        "--input",
        default="csv_files/diff_updated.csv",
        help="Path to input CSV (default: csv_files/diff_updated.csv)",
    )
    parser.add_argument(
        "--output",
        default="csv_files/diff_updated_parsed.csv",
        help="Path to output CSV (default: csv_files/diff_updated_parsed.csv)",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="File encoding for input CSV (default: utf-8)",
    )
    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)

    if not in_path.exists():
        raise SystemExit(f"Input CSV not found: {in_path}")

    # Read input
    df = pd.read_csv(in_path, encoding=args.encoding)
    if "diff_updated" not in df.columns:
        raise SystemExit("Input CSV must contain a 'diff_updated' column.")

    # Parse and build result
    parsed = split_diff_updated(df)

    # Only keep requested columns in the output
    cols = ["existing", "proposed", "index", "is_meaningful_str"]
    missing = [c for c in cols if c not in parsed.columns]
    if missing:
        raise SystemExit(f"Failed to produce expected columns: {missing}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    parsed.to_csv(out_path, index=False, columns=cols)

    # Simple summary to stdout
    total = len(df)
    parsed_ok = parsed["existing"].notna() & parsed["proposed"].notna() & parsed["index"].notna()
    print(
        f"Wrote {out_path} — {parsed_ok.sum()} / {total} rows parsed successfully.\n"
        f"Columns: {', '.join(cols)}"
    )


if __name__ == "__main__":
    main()