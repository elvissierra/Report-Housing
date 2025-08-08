import argparse
import pandas as pd
from extract import load_csv
from transform import generate_column_report
from report_generator import assemble_report, save_report

# Coupled with auto_report_pipeline dir


def run_auto_report(input_path: str, config_path: str, output_path: str, multi_sheet: bool = False):
    # Handle multi-sheet Excel workbooks
    if multi_sheet and input_path.lower().endswith((".xls", ".xlsx")):
        sheets = pd.read_excel(input_path, sheet_name=None)
        for sheet_name, df_sheet in sheets.items():
            config_df = load_csv(config_path)
            report_blocks = generate_column_report(df_sheet, config_df)
            final_report = assemble_report(report_blocks)
            # Construct output filename per sheet
            sheet_output = output_path.replace(".csv", f"_{sheet_name}.csv")
            save_report(final_report, sheet_output)
        return
    df = load_csv(input_path)
    config_df = load_csv(config_path)
    report_blocks = generate_column_report(df, config_df)
    final_report = assemble_report(report_blocks)
    save_report(final_report, output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto Report Generator")
    parser.add_argument("--input-path", required=True, help="Path to input CSV or Excel file")
    parser.add_argument("--config-path", required=True, help="Path to report config CSV")
    parser.add_argument("--output-path", required=True, help="Path to output CSV")
    parser.add_argument("--multi-sheet", action="store_true", help="Process all sheets in an Excel workbook")
    args = parser.parse_args()

    run_auto_report(
        input_path=args.input_path,
        config_path=args.config_path,
        output_path=args.output_path,
        multi_sheet=args.multi_sheet,
    )
