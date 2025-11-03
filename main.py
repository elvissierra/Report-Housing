"""
Script to output a report based on Quip congfigurations
v4: Next step- add visual data
"""

__author__ = "Elvis Sierra"
__email__ = "elvis_sierra@apple.com"
__version__ = "4.5"
__status__ = "dev"
__date_created__ = "6.11.2025"
__last_modified__ = "10.30.2025"


import os
import argparse
import pandas as pd
from report_auto.extract import load_csv
from report_auto.transform import generate_column_report
from report_auto.generator import assemble_report, save_report

# Main Data Reporting Generator


def run_auto_report(
    input_path: str,
    config_df: pd.DataFrame,
    output_path: str,
    multi_sheet: bool = False,
) -> None:
    """
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
    - This function delegates the transformation to `generate_column_report`,
      the layout/assembly to `assemble_report`, and file persistence to `save_report`.
    - If `transform.run_basic_insights` is available, it will also write two artifacts:
      `correlation_results.csv` and `CrossTabs_output.csv` next to the main output.
    """
    # Handle multi-sheet workbook
    if multi_sheet and input_path.lower().endswith((".xls", ".xlsx")):
        # Read all worksheets into a dict of {sheet_name: DataFrame}
        sheets = pd.read_excel(input_path, sheet_name=None)
        for sheet_name, df_sheet in sheets.items():
            # Normalize headers to consistent lower_snake_case to match config driven keys
            df_sheet.columns = (
                df_sheet.columns.str.strip().str.lower().str.replace(" ", "_")
            )
            report_blocks = generate_column_report(df_sheet, config_df)
            final_report = assemble_report(report_blocks)
            # Emit an output per worksheet by suffixing the sheet name
            sheet_output = output_path.replace(".csv", f"_{sheet_name}.csv")
            save_report(final_report, sheet_output)
            try:
                from report_auto.transform import run_basic_insights

                # Insights expect normalized column names; work on a copy to avoid side effects
                cfg_ins = config_df.copy()
                cfg_ins.columns = (
                    cfg_ins.columns.str.strip().str.lower().str.replace(" ", "_")
                )
                out_dir = os.path.dirname(sheet_output) or "."
                run_basic_insights(df_sheet, config_df=cfg_ins, output_dir=out_dir)
            except Exception as e:
                print(f"[insights] Skipped due to error on sheet '{sheet_name}': {e}")
        return
    # Fast path: CSV input or Excel treated as a single sheet
    df = load_csv(input_path)
    report_blocks = generate_column_report(df, config_df)
    final_report = assemble_report(report_blocks)
    save_report(final_report, output_path)
    try:
        from report_auto.transform import run_basic_insights

        # If insights utilities are present, compute correlations/crosstabs alongside the report
        cfg_ins = config_df.copy()
        cfg_ins.columns = cfg_ins.columns.str.strip().str.lower().str.replace(" ", "_")
        out_dir = os.path.dirname(output_path) or "."
        run_basic_insights(df, config_df=cfg_ins, output_dir=out_dir)
    except Exception as e:
        print(f"[insights] Skipped due to error: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto Report Generator")
    # CLI entrypoint: the first two rows of the config CSV hold INPUT/OUTPUT paths;
    # the remaining rows are the declarative report instructions consumed by `transform`.
    parser.add_argument(
        "--config-path",
        required=True,
        help="Path to report_config CSV (first two rows set to be INPUT/OUTPUT)",
    )
    parser.add_argument(
        "--multi-sheet", action="store_true", help="Process all sheets in work book."
    )
    args = parser.parse_args()

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

    run_auto_report(
        input_path,
        config_df,
        output_path,
        args.multi_sheet,
    )
