

"""
Core orchestration of the reporting pipeline.

This module exposes functions that can be reused from the CLI, tests,
and future API endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, List

import os
from pathlib import Path

import pandas as pd

from report_auto.extract import load_csv
from report_auto.transform import generate_column_report, run_basic_insights
from report_auto.generator import assemble_report, save_report
from report_auto.utils import normalize_headers


def recipe_to_config_df(recipe: Dict[str, Any]) -> pd.DataFrame:
    """
    Translate a SPA JSON `recipe` into the legacy config DataFrame that
    `generate_column_report` expects.

    The JSON structure mirrors the frontend types:
      - recipe.rules[] with: column, operation, options{delimiter,separateNodes,rootOnly,value,excludeKeys}, enabled
      - recipe.insights: {sources[], targets[], threshold}

    Returns
    -------
    pd.DataFrame
        Rows compatible with `transform.generate_column_report`, including
        INSIGHTS rows consumed by `run_basic_insights`.
    """
    rows: List[Dict[str, object]] = []
    for r in recipe.get("rules", []):
        if not r.get("enabled", True):
            continue
        opts = r.get("options", {}) or {}
        op = (r.get("operation") or "").strip().lower()
        row = {
            "column": r.get("column", ""),
            "value": (opts.get("value") or ""),
            "delimiter": (opts.get("delimiter") or ""),
            "separate_nodes": bool(opts.get("separateNodes")),
            "root_only": bool(opts.get("rootOnly")),
            "duplicate": op == "duplicate",
            "average": op == "average",
            "clean": op == "clean",
            # distribution/valueCount become the generic aggregate path
            "aggregate": op in ("distribution", "valuecount"),
            "exclude_keys": "|".join(
                [
                    str(x).strip()
                    for x in (opts.get("excludeKeys") or [])
                    if str(x).strip()
                ]
            ),
        }
        rows.append(row)

    ins = recipe.get("insights", {}) or {}
    sources = [s for s in ins.get("sources", []) if str(s).strip()]
    targets = [t for t in ins.get("targets", []) if str(t).strip()]
    threshold = ins.get("threshold", None)

    if sources:
        rows.append({"column": "INSIGHTS SOURCES", "value": "|".join(sources)})
    if targets:
        rows.append({"column": "INSIGHTS TARGETS", "value": "|".join(targets)})
    if threshold is not None and str(threshold).strip() != "":
        rows.append({"column": "INSIGHTS THRESHOLD", "value": str(threshold)})

    cfg = pd.DataFrame(rows)
    # Normalize headers now to match downstream expectations
    return normalize_headers(cfg)


def run_auto_report(
    input_path: str,
    config_df: pd.DataFrame,
    output_path: str,
    multi_sheet: bool = False,
) -> None:
    """
    Core orchestration for turning an input dataset + config into a report.

    This function is intentionally side-effectful (reads/writes files) but
    contains no CLI or UI logic so it can be reused from APIs or tests.
    """
    # Handle multi-sheet workbook
    if multi_sheet and input_path.lower().endswith((".xls", ".xlsx")):
        # Read all worksheets into a dict of {sheet_name: DataFrame}
        sheets = pd.read_excel(input_path, sheet_name=None)
        for sheet_name, df_sheet in sheets.items():
            # Normalize headers to consistent lower_snake_case to match config driven keys
            df_sheet = normalize_headers(df_sheet)
            report_blocks = generate_column_report(df_sheet, config_df)
            final_report = assemble_report(report_blocks)
            # Emit an output per worksheet by suffixing the sheet name
            sheet_output = output_path.replace(".csv", f"_{sheet_name}.csv")
            save_report(final_report, sheet_output)
            try:
                # Insights expect normalized column names; work on a copy to avoid side effects
                cfg_ins = normalize_headers(config_df.copy())
                out_dir = os.path.dirname(sheet_output) or "."
                run_basic_insights(df_sheet, config_df=cfg_ins, output_dir=out_dir)
            except Exception as e:
                print(
                    f"[insights] Skipped due to error on sheet '{sheet_name}': {e}"
                )
        return

    # Fast path: CSV input or Excel treated as a single sheet
    ext = os.path.splitext(input_path)[1].lower()
    if ext in (".xls", ".xlsx"):
        df = pd.read_excel(input_path)
        df = normalize_headers(df)
    else:
        df = load_csv(input_path)
    report_blocks = generate_column_report(df, config_df)
    final_report = assemble_report(report_blocks)
    save_report(final_report, output_path)
    try:
        # If insights utilities are present, compute correlations/crosstabs alongside the report
        cfg_ins = normalize_headers(config_df.copy())
        out_dir = os.path.dirname(output_path) or "."
        run_basic_insights(df, config_df=cfg_ins, output_dir=out_dir)
    except Exception as e:
        print(f"[insights] Skipped due to error: {e}")


def run_recipe_workflow(
    recipe: Dict[str, Any],
    input_path: str,
    output_path: str,
    multi_sheet: bool = False,
) -> None:
    """
    High-level helper for the `recipe.json` path.

    - Converts a Vue Designer recipe.json into a config DataFrame.
    - Delegates to run_auto_report so that CSV/Excel + insights are handled uniformly.
    """
    config_df = recipe_to_config_df(recipe)
    run_auto_report(
        input_path=input_path,
        config_df=config_df,
        output_path=output_path,
        multi_sheet=multi_sheet,
    )