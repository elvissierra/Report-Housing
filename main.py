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
__last_modified__ = "11.4.2025"


import os
import sys
import subprocess
import venv
import argparse
from pathlib import Path

def _ensure_runtime() -> None:
    """
    Zero-setup bootstrap: if pandas/numpy are missing, create a local venv,
    install requirements, and re-exec into that interpreter.
    """
    try:
        import pandas  # noqa: F401
        import numpy   # noqa: F401
        return
    except Exception:
        pass

    root = Path(__file__).resolve().parent
    venv_dir = root / ".report_auto_venv"
    py_bin = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

    if not venv_dir.exists():
        print("⏳ Setting up a local environment (.report_auto_venv)…")
        venv.EnvBuilder(with_pip=True, clear=False).create(venv_dir)

    # Install minimal deps needed for CSV/Excel processing
    try:
        print("⏳ Installing dependencies (pandas, numpy, openpyxl)…")
        subprocess.check_call([str(py_bin), "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([str(py_bin), "-m", "pip", "install", "pandas>=2.0", "numpy>=1.24", "openpyxl>=3.1"])
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)

    # Re-exec this script under the venv's Python, preserving args
    print("✅ Environment ready. Re-launching…")
    os.execv(str(py_bin), [str(py_bin), str(Path(__file__).resolve()), *sys.argv[1:]])

_ensure_runtime()

import pandas as pd
from report_auto.extract import load_csv
from report_auto.transform import generate_column_report
from report_auto.generator import assemble_report, save_report
from report_auto.utils import normalize_headers


def run_auto_report(
    input_path: str,
    config_df: pd.DataFrame,
    output_path: str,
    multi_sheet: bool = False,
) -> None:
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
                from report_auto.transform import run_basic_insights

                # Insights expect normalized column names; work on a copy to avoid side effects
                cfg_ins = normalize_headers(config_df.copy())
                out_dir = os.path.dirname(sheet_output) or "."
                run_basic_insights(df_sheet, config_df=cfg_ins, output_dir=out_dir)
            except Exception as e:
                print(f"[insights] Skipped due to error on sheet '{sheet_name}': {e}")
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
        from report_auto.transform import run_basic_insights

        # If insights utilities are present, compute correlations/crosstabs alongside the report
        cfg_ins = normalize_headers(config_df.copy())
        out_dir = os.path.dirname(output_path) or "."
        run_basic_insights(df, config_df=cfg_ins, output_dir=out_dir)
    except Exception as e:
        print(f"[insights] Skipped due to error: {e}")

    # CLI entrypoint: the first two rows of the config CSV hold INPUT/OUTPUT paths;


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto Report Generator")
    # the remaining rows are the declarative report instructions consumed by the transform module.
    parser.add_argument(
        "--config-path",
        default=None,
        help="Path to report_config CSV (first two rows set to be INPUT/OUTPUT). If omitted, a file picker will open.",
    )
    parser.add_argument(
        "--multi-sheet", action="store_true", help="Process all sheets in work book."
    )

    args = parser.parse_args()

    # GUI fallback: allow double-click / no-args usage
    if not args.config_path:
        try:
            import tkinter as tk
            from tkinter import filedialog, messagebox
            root = tk.Tk()
            root.withdraw()
            chosen = filedialog.askopenfilename(
                title="Select report_config.csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            if not chosen:
                print("No configuration selected. Exiting.")
                sys.exit(2)
            args.config_path = chosen
            gui_selected = True
        except Exception:
            print("Please provide --config-path /path/to/report_config.csv")
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
    if gui_selected and str(input_path).lower().endswith((".xls", ".xlsx")) and not args.multi_sheet:
        try:
            from tkinter import messagebox
            if messagebox.askyesno("Process all sheets?", "Detected an Excel workbook. Process ALL sheets?"):
                args.multi_sheet = True
        except Exception:
            pass

    run_auto_report(
        input_path,
        config_df,
        output_path,
        args.multi_sheet,
    )
