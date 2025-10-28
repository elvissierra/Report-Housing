import os
import argparse
import pandas as pd
from extract import load_csv
from transform import generate_column_report
from report_generator import assemble_report, save_report

# Main Data Reporting Generator

def run_auto_report(
    input_path: str,
    config_df: pd.DataFrame,
    output_path: str,
    multi_sheet: bool = False,
):
    # Handle multi-sheet workbook
    if multi_sheet and input_path.lower().endswith((".xls", ".xlsx")):
        sheets = pd.read_excel(input_path, sheet_name=None)
        for sheet_name, df_sheet in sheets.items():
            df_sheet.columns = (
                df_sheet.columns.str.strip().str.lower().str.replace(" ", "_")
            )
            report_blocks = generate_column_report(df_sheet, config_df)
            final_report = assemble_report(report_blocks)
            # per sheet
            sheet_output = output_path.replace(".csv", f"_{sheet_name}.csv")
            save_report(final_report, sheet_output)
            try:
                from transform import run_basic_insights
                cfg_ins = config_df.copy()
                cfg_ins.columns = cfg_ins.columns.str.strip().str.lower().str.replace(" ", "_")
                out_dir = os.path.dirname(sheet_output) or "."
                run_basic_insights(df_sheet, config_df=cfg_ins, output_dir=out_dir)
            except Exception as e:
                print(f"[insights] Skipped due to error on sheet '{sheet_name}': {e}")
        return
    df = load_csv(input_path)
    report_blocks = generate_column_report(df, config_df)
    final_report = assemble_report(report_blocks)
    save_report(final_report, output_path)
    try:
        from transform import run_basic_insights
        cfg_ins = config_df.copy()
        cfg_ins.columns = cfg_ins.columns.str.strip().str.lower().str.replace(" ", "_")
        out_dir = os.path.dirname(output_path) or "."
        run_basic_insights(df, config_df=cfg_ins, output_dir=out_dir)
    except Exception as e:
        print(f"[insights] Skipped due to error: {e}")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto Report Generator")
    parser.add_argument(
        "--config-path",
        required=True,
        help="Path to report_config CSV (first two rows set to be INPUT/OUTPUT)",
    )
    parser.add_argument(
        "--multi-sheet", action="store_true", help="Process all sheets in work book."
    )
    args = parser.parse_args()

    raw_cfg = pd.read_csv(args.config_path, header=None, nrows=2)
    first_row = raw_cfg.iloc[0].tolist()
    if "INPUT" in first_row:
        in_row = first_row.index("INPUT")
        input_path = raw_cfg.iloc[0, in_row + 1]
    else:
        raise ValueError("CONFIG ERROR: 'INPUT' label not found in first row")

    second_row = raw_cfg.iloc[1].tolist()
    if "OUTPUT" in second_row:
        out_row = second_row.index("OUTPUT")
        output_path = raw_cfg.iloc[1, out_row + 1]
    else:
        raise ValueError("CONFIG ERROR: 'OUTPUT' label not found in second row")
    # Load actual config table, skipping the first two rows for the input/output paths
    config_df = pd.read_csv(args.config_path, header=0, skiprows=2)

    run_auto_report(
        input_path,
        config_df,
        output_path,
        args.multi_sheet,
    )
