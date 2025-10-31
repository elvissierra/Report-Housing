from __future__ import annotations
import pandas as pd
import re
from utils import clean_list_string
import numpy as np
import csv
from typing import Optional, List, Dict


def _ensure_series(obj: pd.Series | pd.DataFrame) -> pd.Series:
    return obj.iloc[:, 0] if isinstance(obj, pd.DataFrame) else obj


# Data Manipulation

"""
COLUMN
Is the column in the report to be manipulated.
-------------------------------------
VALUE
Is an optional input that will target a single value present within the reporting file.
-------------------------------------
AGGREGATE
To always be set as “yes” unless when blank/NaN value is desired. # Is there a better use case?
-------------------------------------
ROOT ONLY
When the desired output is at index[0]. # this is for when the desired output is the 1st word or index of a string
-------------------------------------
DELIMITER
Any character to separate by.
-------------------------------------
SEPARATE NODES
To be used for when there are nested values and alongside DELIMITER.
-------------------------------------
DUPLICATE
To identify duplicates.
-------------------------------------
AVERAGE
To output the average within a column this is float int any other digit base.
-------------------------------------
CLEAN
To clean any marking from a string, this is to only output character
"""


def generate_column_report(
    report_df: pd.DataFrame, config_df: pd.DataFrame
) -> list[list[str | int]]:
    """
    Build the long-form report sections according to the declarative `config_df`.

    The algorithm:
    1) Normalize config flags (aggregate, root_only, separate_nodes, average, duplicate, clean).
    2) For each referenced column in the data:
       - If `clean` is set: emit a cleaned listing of values (one per row).
       - If `duplicate` is set: count normalized duplicates and list counts.
       - If `average` is set: compute numeric mean (preserving % suffix if present).
       - Else: compute distribution or targeted counts, optionally splitting by delimiter,
         root_only extraction, or matching an explicit `value`.
    3) Each section is appended to the combined output with a blank spacer row.

    Returns
    -------
    list[list[str|int]]
        A list of "blocks", each block being a 3-column section ready for assembly.
    """
    # total tasks used / not calling atm
    total_config = len(config_df)
    # tatal rows read / replacing total config atm
    total_rows = len(report_df)
    cfg = config_df.copy()
    cfg.columns = cfg.columns.str.strip().str.lower().str.replace(" ", "_")
    cfg["column"] = (
        cfg["column"].astype(str).str.strip().str.lower().str.replace(" ", "_")
    )

    # Normalize boolean-like flags in the config (accept 'yes'/'true', otherwise False)
    flags = [
        "aggregate",
        "root_only",
        "separate_nodes",
        "average",
        "duplicate",
        "clean",
    ]
    for flag in flags:
        if flag in cfg.columns:
            s = cfg[flag].astype(str).str.strip().str.lower()
            cfg[flag] = s.isin(["yes", "true"])
        else:
            cfg[flag] = False

    if "value" in cfg.columns:
        cfg["value"] = cfg["value"].fillna("").astype(str).str.lower()
    else:
        cfg["value"] = ""

    if "delimiter" in cfg.columns:
        # Do not set any default; missing/NaN means "no delimiter provided"
        pass
    else:
        cfg["delimiter"] = ""

    sections = []
    sections.append([["Total rows", "", total_rows]])

    for col_name in cfg["column"].unique():
        if col_name not in report_df.columns:
            continue

        hdr = col_name.replace("_", " ").upper()

        is_clean = cfg.loc[cfg["column"] == col_name, "clean"].any()
        if is_clean:
            # Fast-path behavior toggles controlled entirely by config flags
            clean_section = [[hdr, "", "Cleaned"]]
            cleaned = report_df[col_name].apply(clean_list_string)
            for val in cleaned:
                clean_section.append(["", "", val])
            sections.append(clean_section)
            continue

        if cfg.loc[cfg["column"] == col_name, "duplicate"].any():
            # Fast-path behavior toggles controlled entirely by config flags
            s = report_df[col_name].fillna("").astype(str).str.strip().str.lower()
            # Normalize values for duplicate detection to avoid case/space noise
            counts = s.value_counts()
            duplicate = counts[counts > 1]
            section = [[hdr, "Duplicates", "Instances"]]
            for value, cnt in sorted(
                duplicate.items(), key=lambda x: (-int(x[1]), str(x[0]))
            ):
                section.append(["", value, int(cnt)])
            sections.append(section)
            continue

        if cfg.loc[cfg["column"] == col_name, "average"].any():
            # Fast-path behavior toggles controlled entirely by config flags
            raw = report_df[col_name].astype(str).str.strip()
            # Support numbers with optional '%' suffix; non-numeric entries are coerced to NaN
            nums = pd.to_numeric(raw.str.rstrip("%"), errors="coerce")
            if nums.notna().sum() == 0:
                sections.append([[hdr, "", "Average"], ["No numeric data", "", ""]])
            else:
                unit = "%" if raw.str.endswith("%").any() else ""
                avg = nums.mean()
                sections.append([[hdr, "", "Average"], ["", "", f"{avg:.2f}{unit}"]])
            continue

        entries = cfg[cfg["column"] == col_name]
        label_counts = {}
        search_value = entries[entries["value"] != ""]

        if not search_value.empty:
            for _, r in search_value.iterrows():
                series = report_df[col_name].fillna("").astype(str)
                # Delimiter logic for separate_nodes
                if r["separate_nodes"]:
                    # Split nested lists by delimiter, explode into rows, and normalize for counting
                    delim = (
                        r["delimiter"]
                        if pd.notna(r["delimiter"])
                        and str(r["delimiter"]).strip() != ""
                        else None
                    )
                    if delim:
                        items = (
                            series.str.split(
                                rf"\s*{re.escape(str(delim))}\s*", regex=True
                            )
                            .explode()
                            .dropna()
                            .str.strip()
                            .str.lower()
                            # .apply(clean_list_string) | Not applying cleaning here, as below
                        )
                    else:
                        # No delimiter provided; treat the entire cell as a single token
                        items = series.fillna("").astype(str).str.strip().str.lower()
                    cnt = int((items == str(r["value"]).strip().lower()).sum())
                else:
                    delim = (
                        r["delimiter"]
                        if pd.notna(r["delimiter"])
                        and str(r["delimiter"]).strip() != ""
                        else None
                    )
                    if r["root_only"] and delim:
                        series = series.str.split(re.escape(str(delim)), expand=True)[0]
                    series = _ensure_series(series)
                    if delim:
                        d = re.escape(str(delim))
                        v = re.escape(str(r["value"]).strip().lower())
                        pattern = rf"(?:^|{d})\s*{v}\s*(?:{d}|$)"
                        cnt = int(
                            series.str.lower().str.contains(pattern, regex=True).sum()
                        )
                    else:
                        # Without a delimiter, perform normalized equality on the whole field
                        cnt = int(
                            series.str.strip()
                            .str.lower()
                            .eq(str(r["value"]).strip().lower())
                            .sum()
                        )
                label = r["value"] or "None"
                label_counts[label] = cnt
        else:
            for _, r in entries.iterrows():
                series = report_df[col_name].fillna("").astype(str)
                if r["separate_nodes"]:
                    # Split nested lists by delimiter, explode into rows, and normalize for counting
                    delim = (
                        r["delimiter"]
                        if pd.notna(r["delimiter"])
                        and str(r["delimiter"]).strip() != ""
                        else None
                    )
                    if delim:
                        items = (
                            series.str.split(
                                rf"\s*{re.escape(str(delim))}\s*", regex=True
                            )
                            .explode()
                            .dropna()
                            .str.strip()
                            .str.lower()
                        )
                    else:
                        items = series.fillna("").astype(str).str.strip().str.lower()
                    for val in items:
                        label = val or "None"
                        label_counts[label] = label_counts.get(label, 0) + 1
                elif r["aggregate"]:
                    # Fast-path behavior toggles controlled entirely by config flags
                    delim = (
                        r["delimiter"]
                        if pd.notna(r["delimiter"])
                        and str(r["delimiter"]).strip() != ""
                        else None
                    )
                    if r["root_only"] and delim:
                        series = series.str.split(re.escape(str(delim)), expand=True)[0]
                    series = _ensure_series(series)
                    s = series.str.strip().str.lower()
                    for val in sorted(s.unique()):
                        if not val.strip():
                            continue
                        cnt = int((s == val).sum())
                        label_counts[val] = cnt
                else:
                    delim = (
                        r["delimiter"]
                        if pd.notna(r["delimiter"])
                        and str(r["delimiter"]).strip() != ""
                        else None
                    )
                    if r["root_only"] and delim:
                        series = series.str.split(re.escape(str(delim)), expand=True)[0]
                    series = _ensure_series(series)
                    if delim:
                        d = re.escape(str(delim))
                        v = re.escape(str(r["value"]).strip().lower())
                        pattern = rf"(?:^|{d})\s*{v}\s*(?:{d}|$)"
                        cnt = int(
                            series.str.lower().str.contains(pattern, regex=True).sum()
                        )
                    else:
                        cnt = int(
                            series.str.strip()
                            .str.lower()
                            .eq(str(r["value"]).strip().lower())
                            .sum()
                        )
                    label = r["value"] or "None"
                    label_counts[label] = label_counts.get(label, 0) + cnt

        # Emit a three-column section with percentage of total rows and absolute count
        section = [[hdr, "%", "Count"]]
        for label, cnt in sorted(
            label_counts.items(), key=lambda x: (-x[1], str(x[0]))
        ):
            pct = round(cnt / total_rows * 100, 2) if total_rows else 0
            section.append([label, f"{pct:.2f}%", cnt])
        sections.append(section)

    return sections


# ===== Insights / Correlations =====


def is_categorical_column(series: pd.Series, max_unique_values: int = 20) -> bool:
    """Heuristic: treat as categorical if dtype=object or unique count is small."""
    try:
        unique_count = series.nunique(dropna=True)
    except Exception:
        unique_count = max_unique_values + 1
    return series.dtype == "object" or unique_count <= max_unique_values


def cramers_v_stat(col_a: pd.Series, col_b: pd.Series) -> float:
    """Compute Cramér's V association for two categorical variables with bias correction."""
    contingency_table = pd.crosstab(col_a, col_b)
    if contingency_table.shape[0] < 2 or contingency_table.shape[1] < 2:
        return np.nan

    observed = contingency_table.values.astype(float)
    total = observed.sum()
    if total == 0:
        return np.nan

    row_totals = observed.sum(axis=1, keepdims=True)
    col_totals = observed.sum(axis=0, keepdims=True)
    expected = row_totals @ col_totals / total

    with np.errstate(divide="ignore", invalid="ignore"):
        chi_square = np.nansum((observed - expected) ** 2 / expected)

    rows, cols = observed.shape
    phi2 = chi_square / total

    phi2_corrected = max(0.0, phi2 - ((cols - 1) * (rows - 1)) / (total - 1))
    rows_corrected = rows - ((rows - 1) ** 2) / (total - 1)
    cols_corrected = cols - ((cols - 1) ** 2) / (total - 1)
    denom = min((cols_corrected - 1), (rows_corrected - 1))

    return np.sqrt(phi2_corrected / denom) if denom > 0 else np.nan


def compute_correlations_and_crosstabs(
    dataframe: pd.DataFrame,
    source_columns: list,
    target_columns: list,
    correlation_threshold: float = 0.2,
    crosstabs_output_path: str = "csv_files/crosstabs_output.csv",
    correlations_output_path: str = "csv_files/correlation_results.csv",
    verbose: bool = True,
    include_type: bool = False,
) -> pd.DataFrame:
    """
    Compare selected columns and persist two artifacts:
    - Crosstabs for categorical×categorical pairs (written as CSV sections).
    - A sorted CSV of correlations above `correlation_threshold`.

    Supports numeric×numeric (Pearson r), categorical×categorical (Cramér's V),
    and mixed pairs (max |r| across one-hot dummies vs numeric).
    """
    from pandas.api.types import is_numeric_dtype

    correlation_rows = []

    available_sources = [c for c in source_columns if c in dataframe.columns]
    available_targets = [c for c in target_columns if c in dataframe.columns]

    if verbose:
        missing_sources = sorted(set(source_columns) - set(available_sources))
        missing_targets = sorted(set(target_columns) - set(available_targets))
        if missing_sources:
            print(f"[insights] Skipping missing source columns: {missing_sources}")
        if missing_targets:
            print(f"[insights] Skipping missing target columns: {missing_targets}")

    with open(crosstabs_output_path, mode="w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)

        for src_col in available_sources:
            for tgt_col in available_targets:
                src_series = dataframe[src_col]
                tgt_series = dataframe[tgt_col]

                mask = src_series.notna() & tgt_series.notna()
                if mask.sum() == 0:
                    continue

                src_vals = src_series[mask]
                tgt_vals = tgt_series[mask]

                try:
                    # Numeric - Numeric
                    if is_numeric_dtype(src_vals) and is_numeric_dtype(tgt_vals):
                        pearson = src_vals.corr(tgt_vals)
                        if (
                            pearson is not None
                            and np.isfinite(pearson)
                            and abs(pearson) >= correlation_threshold
                        ):
                            row = {
                                "Source Column": src_col,
                                "Target Column": tgt_col,
                                "Correlation": round(float(pearson), 4),
                            }
                            if include_type:
                                row["Type"] = "Positive" if pearson > 0 else "Negative"
                            correlation_rows.append(row)

                    # Categorical - Categorical
                    elif is_categorical_column(src_vals) and is_categorical_column(
                        tgt_vals
                    ):
                        ctab = pd.crosstab(src_vals, tgt_vals)
                        writer.writerow([f"=== Crosstab: {src_col} vs {tgt_col} ==="])
                        writer.writerow(
                            [ctab.index.name or src_col] + list(ctab.columns)
                        )
                        for idx, row in ctab.iterrows():
                            writer.writerow([idx] + list(row.values))
                        writer.writerow([])

                        v = cramers_v_stat(src_vals, tgt_vals)
                        if (
                            v is not None
                            and np.isfinite(v)
                            and v >= correlation_threshold
                        ):
                            row = {
                                "Source Column": src_col,
                                "Target Column": tgt_col,
                                "Correlation": round(float(v), 4),
                            }
                            if include_type:
                                row["Type"] = "N/A"
                            correlation_rows.append(row)

                    # Mixed (Categorical - Numeric)
                    elif (
                        is_categorical_column(src_vals) and is_numeric_dtype(tgt_vals)
                    ) or (
                        is_numeric_dtype(src_vals) and is_categorical_column(tgt_vals)
                    ):
                        cat_vals, num_vals = (
                            (src_vals, tgt_vals)
                            if is_categorical_column(src_vals)
                            else (tgt_vals, src_vals)
                        )
                        dummies = pd.get_dummies(cat_vals)
                        max_abs_corr = (
                            dummies.corrwith(num_vals).abs().max()
                            if not dummies.empty
                            else 0.0
                        )
                        if verbose:
                            print(
                                f"[insights] {src_col} vs {tgt_col}: mixed max |r|={max_abs_corr:.4f}"
                            )
                        if (
                            max_abs_corr is not None
                            and np.isfinite(max_abs_corr)
                            and max_abs_corr >= correlation_threshold
                        ):
                            row = {
                                "Source Column": src_col,
                                "Target Column": tgt_col,
                                "Correlation": round(float(max_abs_corr), 4),
                            }
                            if include_type:
                                row["Type"] = "Mixed"
                            correlation_rows.append(row)
                except Exception as e:
                    if verbose:
                        print(f"[insights] Skipped {src_col} vs {tgt_col}: {e}")
                    continue

    results_df = pd.DataFrame(correlation_rows)
    results_df = (
        results_df.sort_values(by="Correlation", ascending=False)
        if not results_df.empty
        else results_df
    )
    results_df.to_csv(correlations_output_path, index=False)

    print(f"✅ Correlation results → {correlations_output_path}")
    print(f"✅ Crosstabs written → {crosstabs_output_path}")

    return results_df


def _parse_insights_from_config(config_df: pd.DataFrame) -> Dict[str, object]:
    """
    Extract insights directives from the report config.

    Recognized keys (case-insensitive in the COLUMN field):
      - 'INSIGHTS SOURCES'   → VALUE contains pipe-separated column names
      - 'INSIGHTS TARGETS'   → VALUE contains pipe-separated column names
      - 'INSIGHTS THRESHOLD' → VALUE contains a float (e.g., 0.3)
    """

    def _norm_key_name(s: str) -> str:
        s = str(s or "").strip().lower()
        s = re.sub(r"[^a-z0-9]+", " ", s)
        s = re.sub(r"\s+", " ", s).strip().replace(" ", "")
        return s

    out = {
        "threshold": 0.2,
        "sources": None,
        "targets": None,
    }
    if config_df is None or config_df.empty or "column" not in config_df.columns:
        return out

    rows = config_df[["column", "value"]].copy()
    rows["column"] = rows["column"].astype(str).str.strip()
    rows["value"] = rows["value"].astype(str).str.strip()

    lut = {}
    for _, r in rows.iterrows():
        key_norm = _norm_key_name(r["column"])
        if key_norm in {"insightssources", "insightstargets", "insightsthreshold"}:
            lut[key_norm] = r["value"]

    def _as_float(s: str):
        try:
            return float(s)
        except Exception:
            return None

    def _as_list(s: str) -> List[str]:
        if not s:
            return []
        return [part.strip() for part in s.split("|") if part.strip()]

    th = _as_float(lut.get("insightsthreshold", ""))
    if th is not None:
        out["threshold"] = th

    srcs = _as_list(lut.get("insightssources", ""))
    tgts = _as_list(lut.get("insightstargets", ""))
    if srcs:
        out["sources"] = srcs
    if tgts:
        out["targets"] = tgts

    return out


def run_basic_insights(
    dataframe: pd.DataFrame,
    config_df: Optional[pd.DataFrame] = None,
    threshold: Optional[float] = None,
    output_dir: str = ".",
) -> Optional[pd.DataFrame]:
    """
    Convenience wrapper to run correlation/crosstab analysis next to the main report.

    - De-duplicates duplicate column names (appending .1, .2…) to avoid collisions.
    - Resolves configured source/target names against normalized headers.
    - Emits `correlation_results.csv` and `crosstabs_output.csv` into `output_dir`.
    """
    directives = _parse_insights_from_config(config_df)

    eff_threshold = (
        threshold if threshold is not None else directives.get("threshold", 0.2)
    )

    def _make_unique(cols: list[str]) -> list[str]:
        seen = {}
        out = []
        for c in cols:
            name = str(c)
            if name in seen:
                seen[name] += 1
                out.append(f"{name}.{seen[name]}")
            else:
                seen[name] = 0
                out.append(name)
        return out

    if dataframe.columns.duplicated().any():
        print(
            "[insights] Detected duplicate column names; de-duplicating for analysis."
        )
        df_work = dataframe.copy()
        df_work.columns = _make_unique(df_work.columns)
    else:
        df_work = dataframe

    source_candidates = directives.get("sources") or []
    target_candidates = directives.get("targets") or []
    if not source_candidates or not target_candidates:
        print("[insights] Skipping: no sources/targets specified in config.")
        return None

    # Resolve names to existing columns, tolerating de-dupe suffixes like .1, .2
    def _norm(s: str) -> str:
        s = str(s).strip().lower()
        s = re.sub(r"\s+", "_", s)
        s = re.sub(r"\.(?:\d+)$", "", s)
        return s

    lut = {}
    for col in df_work.columns:
        lut.setdefault(_norm(col), []).append(col)

    def _resolve(candidates: List[str]) -> List[str]:
        out = []
        for name in candidates:
            out.extend(lut.get(_norm(name), []))
        return out

    sources = _resolve(source_candidates)
    targets = _resolve(target_candidates)

    if not sources or not targets:
        print("[insights] Skipping: unresolved sources/targets after normalization.")
        return None

    crosstab_path = f"{output_dir}/crosstabs_output.csv"
    correlation_path = f"{output_dir}/correlation_results.csv"

    return compute_correlations_and_crosstabs(
        df_work,
        sources,
        targets,
        correlation_threshold=eff_threshold,
        crosstabs_output_path=crosstab_path,
        correlations_output_path=correlation_path,
    )
