import argparse
import pandas as pd
from extract import load_csv
from transform import generate_column_report
from report_generator import assemble_report, save_report

# Coupled with auto_report_pipeline dir


def run_auto_report(input_path: str, config_df: pd.DataFrame, output_path: str, multi_sheet: bool = False):
    # Handle multi-sheet Excel workbooks
    if multi_sheet and input_path.lower().endswith((".xls", ".xlsx")):
        sheets = pd.read_excel(input_path, sheet_name=None)
        for sheet_name, df_sheet in sheets.items():
            report_blocks = generate_column_report(df_sheet, config_df)
            final_report = assemble_report(report_blocks)
            # Construct output filename per sheet
            sheet_output = output_path.replace(".csv", f"_{sheet_name}.csv")
            save_report(final_report, sheet_output)
        return
    df = load_csv(input_path)
    report_blocks = generate_column_report(df, config_df)
    final_report = assemble_report(report_blocks)
    save_report(final_report, output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto Report Generator")
    parser.add_argument(
        "--config-path",
        required=True,
        help="Path to report config CSV (first two rows must be INPUT/OUTPUT)"
    )
    parser.add_argument(
        "--multi-sheet",
        action="store_true",
        help="Process all sheets in an Excel workbook"
    )
    args = parser.parse_args()

    # Read input/output paths from top two rows of config
    raw_cfg = pd.read_csv(args.config_path, header=None, nrows=2)
    input_path = raw_cfg.iloc[0, 1]
    output_path = raw_cfg.iloc[1, 1]
    # Load actual config table, skipping the first two rows
    config_df = pd.read_csv(args.config_path, header=0, skiprows=2)

    run_auto_report(
        input_path,
        config_df,
        output_path,
        args.multi_sheet,
    )
