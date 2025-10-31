# app.py
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import pandas as pd, io, zipfile, os, tempfile

from extract import load_csv
from transform import generate_column_report, run_basic_insights
from generator import assemble_report, save_report

app = FastAPI()

# replace with your GitHub Pages origin
PAGES_ORIGIN = "https://<your-user>.github.io"
app.add_middleware(
    CORSMiddleware,
    allow_origins=[PAGES_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/report")
async def report(
    input_file: UploadFile = File(...),
    config_file: UploadFile = File(...),
    multi_sheet: bool = Form(False),
):
    with tempfile.TemporaryDirectory() as td:
        in_path = os.path.join(td, "input.csv")
        cfg_path = os.path.join(td, "report_config.csv")
        out_path = os.path.join(td, "report.csv")

        with open(in_path, "wb") as f:
            f.write(await input_file.read())
        with open(cfg_path, "wb") as f:
            f.write(await config_file.read())

        raw_cfg = pd.read_csv(cfg_path, header=None, nrows=2)
        config_df = pd.read_csv(cfg_path, header=0, skiprows=2)

        if multi_sheet and in_path.lower().endswith((".xls", ".xlsx")):
            sheets = pd.read_excel(in_path, sheet_name=None)
            for sheet_name, df_sheet in sheets.items():
                df_sheet.columns = (
                    df_sheet.columns.str.strip().str.lower().str.replace(" ", "_")
                )
                blocks = generate_column_report(df_sheet, config_df)
                final = assemble_report(blocks)
                save_report(final, out_path.replace(".csv", f"_{sheet_name}.csv"))
                run_basic_insights(df_sheet, config_df=config_df, output_dir=td)
        else:
            df = load_csv(in_path)
            blocks = generate_column_report(df, config_df)
            final = assemble_report(blocks)
            save_report(final, out_path)
            run_basic_insights(df, config_df=config_df, output_dir=td)

        # stream all artifacts as a zip
        mem = io.BytesIO()
        with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
            for name in os.listdir(td):
                if name.endswith(".csv"):
                    z.write(os.path.join(td, name), arcname=name)
        mem.seek(0)
        return StreamingResponse(
            mem,
            media_type="application/zip",
            headers={
                "Content-Disposition": "attachment; filename=auto_report_artifacts.zip"
            },
        )
