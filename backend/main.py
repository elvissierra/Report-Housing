"""
Script to output a report based on Quip configurations
v4.5: Next step- add visual data

Orchestrate the end-to-end report build.
Parameters
----------
input_path : str
    Path to the raw data file. Supports CSV and, when `multi_sheet=True`, Excel.
config_df : pd.DataFrame
    Normalized configuration table (rows after the first two INPUT/OUTPUT rows).
    Column names are expected to be lower_snake_case (the caller normalizes this).
output_path : str
    Destination CSV for the assembled report.
multi_sheet : bool
    If True and `input_path` is an Excel workbook, process every sheet and emit
    one report per sheet (suffixing the sheet name).
Notes
-----
- If `transform.run_basic_insights` is available, it will also write two artifacts:
  `Correlation_Results.csv` and `Crosstabs_Output.csv` next to the main output.
"""

__author__ = "Elvis Sierra"
__email__ = "elvis_sierra@apple.com"
__version__ = "4.5"
__status__ = "dev"
__date_created__ = "6.11.2025"
__last_modified__ = "11.6.2025"


import sys
import argparse
from pathlib import Path
import json
from typing import Dict, List
import pandas as pd

# FastAPI imports for API wiring
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from report_auto.api.routes import router as report_router
from report_auto.core.pipeline import (
    run_auto_report,
    run_recipe_workflow,
    recipe_to_config_df,
)


# FastAPI application (for uvicorn / gunicorn)

app = FastAPI(title="Report Auto API")

# CORS configuration for local UI development
origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(report_router, prefix="/api")

# Simple healthcheck endpoint
@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto Report Generator")
    # the remaining rows are the declarative report instructions consumed by the transform module.
    parser.add_argument(
        "--config-path",
        default=None,
        help="Path to legacy report_config.csv (first two rows must contain INPUT/OUTPUT). Mutually exclusive with --recipe.",
    )
    parser.add_argument(
        "--recipe",
        default=None,
        help="Path to recipe.json emitted by the Vue Designer (no GUI; requires --input and --output).",
    )
    parser.add_argument(
        "--input",
        default=None,
        help="Path to data file when using --recipe mode (CSV or Excel).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Destination report CSV when using --recipe mode.",
    )
    parser.add_argument(
        "--multi-sheet", action="store_true", help="Process all sheets in work book."
    )

    args = parser.parse_args()

    # --- JSON recipe flow (no GUI) ---
    if args.recipe:
        if args.config_path:
            print("❌ Provide either --config-path or --recipe, not both.")
            sys.exit(2)
        if not args.input or not args.output:
            print("❌ --recipe mode requires --input and --output.")
            sys.exit(2)
        try:
            with open(args.recipe, "r", encoding="utf-8") as fh:
                recipe = json.load(fh)
        except Exception as e:
            print(f"❌ Failed to read recipe JSON: {e}")
            sys.exit(2)
        # Delegate recipe execution to the core pipeline (handles CSV/Excel + insights)
        run_recipe_workflow(
            recipe,
            input_path=args.input,
            output_path=args.output,
            multi_sheet=args.multi_sheet,
        )
        sys.exit(0)

    # GUI fallback: allow double-click / no-args usage
    if not args.config_path:
        try:
            import tkinter as tk
            from tkinter import filedialog, messagebox

            root = tk.Tk()
            root.withdraw()
            chosen = filedialog.askopenfilename(
                title="Select report_config.csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            )
            if not chosen:
                print("No configuration selected. Exiting.")
                sys.exit(2)
            args.config_path = chosen
            gui_selected = True
        except Exception:
            print(
                "Please provide either --config-path /path/to/report_config.csv or --recipe /path/to/recipe.json with --input and --output."
            )
            sys.exit(2)
    else:
        gui_selected = False

    # Load only the first two rows to extract INPUT/OUTPUT without parsing the whole config yet
    raw_cfg = pd.read_csv(args.config_path, header=None, nrows=2)
    # Row 0 must contain the sentinel "INPUT" and its value in the next cell
    first_row = raw_cfg.iloc[0].tolist()
    if "INPUT" in first_row:
        in_row = first_row.index("INPUT")
        input_path = raw_cfg.iloc[0, in_row + 1]
    else:
        raise ValueError("CONFIG ERROR: 'INPUT' label not found in first row")

    # Row 1 must contain the sentinel "OUTPUT" and its value in the next cell
    second_row = raw_cfg.iloc[1].tolist()
    if "OUTPUT" in second_row:
        out_row = second_row.index("OUTPUT")
        output_path = raw_cfg.iloc[1, out_row + 1]
    else:
        raise ValueError("CONFIG ERROR: 'OUTPUT' label not found in second row")
    # The actual config begins on row 3 (index 2); preserve the header row from the file
    config_df = pd.read_csv(args.config_path, header=0, skiprows=2)

    # If launched via GUI and input is an Excel workbook, offer to process all sheets
    if (
        gui_selected
        and str(input_path).lower().endswith((".xls", ".xlsx"))
        and not args.multi_sheet
    ):
        try:
            from tkinter import messagebox

            if messagebox.askyesno(
                "Process all sheets?", "Detected an Excel workbook. Process ALL sheets?"
            ):
                args.multi_sheet = True
        except Exception:
            pass

    run_auto_report(
        input_path,
        config_df,
        output_path,
        args.multi_sheet,
    )
