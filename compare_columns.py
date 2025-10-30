"""
 ~ Stand alone script
Given a CSV with 2 or more text columns, compare the columns row‑by‑row and
emit the differences between a "baseline" column and the others.

Features
- Baseline = the first column passed in --columns (default: the first two string
  columns found if --columns omitted).
- Diff granularity: word|char|sentence (default: word).
- Normalization options: lowercase, strip punctuation, collapse whitespace.
- Outputs per compared column:
    * <col>__added   : tokens present in the compared column but not in baseline
    * <col>__removed : tokens present in the baseline but not in compared column
    * <col>__markup  : unified inline diff markup with [-removed-] and {+added+}

Example
--------
Input strings:
  A: "Does milk man, live here?"
  B: "Does the milk man live here alone, or with multiple people, and how many people?"

With default (word) granularity, B__added would be:
  "the alone , or with multiple people , and how many people ?"
A__removed (if A were compared against B) would be:
  ", ?"  (punctuation differences) — unless you use --strip-punct

Usage
-----
python compare_columns.py --input in.csv --output out.csv --columns colA colB [colC ...]
# or let it auto-detect first two string columns
python compare_columns.py --input in.csv --output out.csv

Control granularity & normalization:
python compare_columns.py --input in.csv --output out.csv \
  --columns colA colB --granularity word --lower --strip-punct --collapse-ws
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from difflib import SequenceMatcher
from typing import Iterable, List, Tuple

# ----------------------------- Tokenization ---------------------------------

def sentence_delimitter(text: str) -> List[str]:
    """Split text into sentences using punctuation as boundaries; drop empties."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip()) if text else []
    return [p for p in parts if p]


def word_tokenize(text: str) -> List[str]:
    """Tokenize into words and standalone punctuation so diffs can track symbols."""
    # Split on whitespace but keep punctuation as separate tokens
    return re.findall(r"\w+|[^\w\s]", text or "")


def char_tokenize(text: str) -> List[str]:
    """Return a list of individual characters (character-level granularity)."""
    return list(text or "")


# ----------------------------- Normalization --------------------------------

def normalize_tokens(tokens: List[str], lower: bool, strip_punct: bool, collapse_ws: bool) -> List[str]:
    """
    Optionally lowercase and strip single-character punctuation tokens.
    `collapse_ws` is applied later at string-join time in `join_tokens`.
    """
    out: List[str] = []
    for t in tokens:
        if lower:
            t = t.lower()
        if strip_punct and re.fullmatch(r"\W", t):
            # drop single-character punctuation tokens
            continue
        out.append(t)
    if collapse_ws:
        # should join with a single space
        pass
    return out


# ------------------------------- Diff logic ---------------------------------

def diff_tokens(a_tokens: List[str], b_tokens: List[str]) -> Tuple[List[str], List[str], List[str]]:
    """
    Compute a diff between `a_tokens` (baseline) and `b_tokens` (candidate).

    Returns
    -------
    added_in_b : list[str]
        Tokens present only in `b_tokens`.
    removed_from_a : list[str]
        Tokens present only in `a_tokens`.
    markup_inline : list[str]
        A sequence containing baseline tokens interleaved with
        `[-removed-]` and `{+added+}` spans to visualize changes inline.
    """
    # Use difflib to obtain stable opcodes; disable autojunk so short texts aren't over-pruned
    sm = SequenceMatcher(a=a_tokens, b=b_tokens, autojunk=False)
    added: List[str] = []
    removed: List[str] = []

    # Start markup as a copy of baseline; we will build progressively
    markup_segments: List[str] = []

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            markup_segments.extend(a_tokens[i1:i2])
        elif tag == 'delete':
            seg = a_tokens[i1:i2]
            removed.extend(seg)
            if seg:
                markup_segments.append("[-" + " ".join(seg) + "-]")
        elif tag == 'insert':
            seg = b_tokens[j1:j2]
            added.extend(seg)
            if seg:
                markup_segments.append("{+" + " ".join(seg) + "+}")
        elif tag == 'replace':
            a_seg = a_tokens[i1:i2]
            b_seg = b_tokens[j1:j2]
            if a_seg:
                removed.extend(a_seg)
                markup_segments.append("[-" + " ".join(a_seg) + "-]")
            if b_seg:
                added.extend(b_seg)
                markup_segments.append("{+" + " ".join(b_seg) + "+}")
        else:
            pass

    return added, removed, markup_segments


# ------------------------------- I/O Helpers --------------------------------

def detect_default_columns(header: List[str]) -> List[str]:
    """Heuristically pick the first two non-empty headers when --columns is omitted."""
    chosen: List[str] = []
    for h in header:
        if h and h.strip():
            chosen.append(h)
            if len(chosen) == 2:
                break
    if len(chosen) < 2:
        raise SystemExit("Could not auto-detect two text columns; please pass --columns explicitly.")
    return chosen


def join_tokens(tokens: Iterable[str], collapse_ws: bool) -> str:
    """Join tokens with single spaces; optionally collapse repeated whitespace."""
    if not tokens:
        return ""
    s = " ".join(tokens)
    return re.sub(r"\s+", " ", s).strip() if collapse_ws else s


# --------------------------------- Main -------------------------------------

def main(argv: List[str] | None = None) -> int:
    """CLI for column-wise diffing. See module docstring for examples and options."""
    p = argparse.ArgumentParser(description="Compare CSV text columns and output differences.")
    p.add_argument('--input', '-i', required=True, help='Path to input CSV')
    p.add_argument('--output', '-o', required=True, help='Path to output CSV')
    p.add_argument('--columns', '-c', nargs='+', help='Columns to compare (first is baseline). If omitted, auto-detect first two headers.')
    p.add_argument('--granularity', '-g', choices=['word', 'char', 'sentence'], default='word', help='Diff granularity (default: word)')
    p.add_argument('--lower', action='store_true', help='Lowercase before diffing')
    p.add_argument('--strip-punct', action='store_true', help='Drop punctuation tokens before diffing')
    p.add_argument('--collapse-ws', action='store_true', help='Collapse whitespace when writing outputs')

    args = p.parse_args(argv)

    # select tokenizer
    if args.granularity == 'word':
        tokenizer = word_tokenize
    elif args.granularity == 'char':
        tokenizer = char_tokenize
    else:
        tokenizer = sentence_delimitter

    with open(args.input, newline='', encoding='utf-8') as f_in:
        reader = csv.DictReader(f_in)
        header = reader.fieldnames or []
        if not header:
            raise SystemExit('Input CSV missing header row.')

        columns = args.columns or detect_default_columns(header)
        baseline_col = columns[0]
        compare_cols = columns[1:]
        if not compare_cols:
            raise SystemExit('Need at least two columns to compare.')

        # Preserve all original columns and append diff artifacts per compared column
        out_header = list(header)
        for col in compare_cols:
            out_header.extend([
                f"{col}__added",
                f"{col}__removed",
                f"{col}__markup",
            ])

        with open(args.output, 'w', newline='', encoding='utf-8') as f_out:
            writer = csv.DictWriter(f_out, fieldnames=out_header)
            writer.writeheader()

            for row in reader:
                base_text = row.get(baseline_col, '') or ''
                base_tokens = tokenizer(base_text)
                base_tokens = normalize_tokens(base_tokens, args.lower, args.strip_punct, args.collapse_ws)

                for col in compare_cols:
                    other_text = row.get(col, '') or ''
                    other_tokens = tokenizer(other_text)
                    other_tokens = normalize_tokens(other_tokens, args.lower, args.strip_punct, args.collapse_ws)

                    added, removed, markup_tokens = diff_tokens(base_tokens, other_tokens)

                    row[f"{col}__added"] = join_tokens(added, args.collapse_ws)
                    row[f"{col}__removed"] = join_tokens(removed, args.collapse_ws)
                    row[f"{col}__markup"] = join_tokens(markup_tokens, args.collapse_ws)

                writer.writerow(row)

    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
