from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse, Response, PlainTextResponse
from utils.definitions import get_all_definitions_as_text
from pydantic import ValidationError
import json
import pandas as pd
import logging
from io import BytesIO
import zipfile

import schemas
from extract import load_tabular_data
from orchestrator import run_dynamic_analysis
from generator import to_csv_string

router = APIRouter()


def _format_block_header(title: str) -> str:
    """
    - Uppercases and replaces space with _
    """
    for sep in ["—", "-"]:
        if sep in title:
            title = title.split(sep, 1)[0]
            break
    base = title.strip().replace("_", " ")
    return base.upper()


def _extract_operation_label(title: str) -> str:
    op = "result"

    for sep in ["—", "-"]:
        if sep in title:
            right = title.split(sep, 1)[1]
            op = right.strip().lower()
            break
    else:
        op = title.strip().lower()

    if "distribution" in op:
        return "distribution"
    if "duplicate" in op:
        return "duplicate count"
    if "average" in op:
        return "average"

    op = " ".join(op.split())
    return op or "result"


def _format_single_block(block: schemas.ReportBlock, is_first: bool) -> str:
    parts: list[str] = []

    if not is_first:
        parts.append("\n")

    data = block.data

    if not data.empty and data.shape[1] <= 3:
        hdr = _format_block_header(block.title)
        op_label = _extract_operation_label(block.title)
        cols = list(data.columns)
        rows: list[list[str]] = []

        # Distribution-style: ["", "%", "Count"]
        if cols == ["", "%", "Count"]:
            # Single header row: column name + operation + metric labels.
            rows.append([f"{hdr} — {op_label}", "%", "Count"])

            for _, row in data.iterrows():
                rows.append(
                    [
                        str(row.iloc[0]),
                        str(row.iloc[1]),
                        str(row.iloc[2]),
                    ]
                )

        elif cols == ["Duplicates", "Instances"]:
            # Single header row: column name + operation + metric labels.
            rows.append([f"{hdr} — {op_label}", "Duplicates", "Instances"])
            for _, row in data.iterrows():
                rows.append(
                    [
                        "",
                        str(row["Duplicates"]),
                        str(int(row["Instances"])),
                    ]
                )

        elif cols == ["Average"]:
            rows.append([f"{hdr} — {op_label}", "", "Average"])
            for _, row in data.iterrows():
                rows.append(["", "", str(row["Average"])])

        else:
            padded_cols = cols[:3] + [""] * max(0, 3 - len(cols))
            metric_label = padded_cols[-1] or "Value"
            rows.append([f"{hdr} — {op_label}", "", metric_label])
            for _, row in data.iterrows():
                vals = [str(v) for v in list(row.values)[:3]]
                vals = vals + [""] * max(0, 3 - len(vals))
                rows.append(vals)

        tmp_df = pd.DataFrame(rows)
        parts.append(to_csv_string(tmp_df, header=False))

    else:
        # Rich blocks (e.g., correlations, crosstabs) – keep title row + full table.
        parts.append(f'"{block.title}"\n')
        if not data.empty:
            parts.append(to_csv_string(data, header=True))
        else:
            parts.append("(No data produced for this analysis)\n")

    return "".join(parts)


def _render_category(blocks: list[schemas.ReportBlock]) -> str:
    """
    Render a list of ReportBlocks for a single category into one CSV string,
    with blank lines between blocks.
    """
    if not blocks:
        return ""

    parts: list[str] = []
    first = True
    for block in blocks:
        parts.append(_format_single_block(block, is_first=first))
        first = False
    return "".join(parts)


# --- INSIGHTS ---
import pandas as pd
from generator import to_csv_string


def _render_insights(blocks: list[schemas.ReportBlock]) -> str:
    """
    Render correlation and crosstab blocks into a single CSV string matching the
    legacy Crosstabs_Output / Correlation_Results layout.

    - All crosstabs are grouped under a single 'Crosstabs_Output' section.
    - Correlations are grouped under a 'Correlation_Results' section with
      columns: Source Column, Target Column, Correlation.
    """
    if not blocks:
        return ""

    parts: list[str] = []

    corr_blocks: list[schemas.ReportBlock] = []
    xtab_blocks: list[schemas.ReportBlock] = []

    for block in blocks:
        title_lower = block.title.lower()
        if "correlation" in title_lower:
            corr_blocks.append(block)
        else:
            xtab_blocks.append(block)

    # 1) Crosstab section
    if xtab_blocks:
        xtab_header_df = pd.DataFrame([["Crosstabs_Output"]])
        parts.append(to_csv_string(xtab_header_df, header=False))

        first_xtab = True
        for block in xtab_blocks:
            data = block.data.copy()

            if "Group" in data.columns:
                data = data.drop(columns=["Group"])

            if data.empty:
                continue

            if "All" in data.columns:
                data = data.drop(columns=["All"])

            index_col = data.columns[0]
            data = data[data[index_col] != "All"]

            # Section separator
            parts.append("\n" if first_xtab else "\n\n")
            first_xtab = False

            title_df = pd.DataFrame([[f"=== {block.title} ==="]])
            parts.append(to_csv_string(title_df, header=False))

            parts.append("\n")
            parts.append(to_csv_string(data, header=True))

    if corr_blocks:
        if parts:
            parts.append("\n\n")

        all_corr = pd.concat([b.data for b in corr_blocks], ignore_index=True)

        if not all_corr.empty:
            if "Correlation Value" in all_corr.columns:
                all_corr = all_corr[~all_corr["Correlation Value"].isna()]

            if not all_corr.empty and {
                "Column 1",
                "Column 2",
                "Correlation Value",
            }.issubset(all_corr.columns):
                corr_df = all_corr[["Column 1", "Column 2", "Correlation Value"]].copy()
                corr_df.rename(
                    columns={
                        "Column 1": "Source Column",
                        "Column 2": "Target Column",
                        "Correlation Value": "Correlation",
                    },
                    inplace=True,
                )

                corr_df["Correlation"] = corr_df["Correlation"].astype(float).round(4)

                header_rows = pd.DataFrame(
                    [
                        ["Correlation_Results", "", ""],
                        ["Source Column", "Target Column", "Correlation"],
                    ],
                    columns=["Source Column", "Target Column", "Correlation"],
                )

                corr_with_header = pd.concat([header_rows, corr_df], ignore_index=True)

                parts.append(to_csv_string(corr_with_header, header=False))

    return "".join(parts)


def get_analysis_request(
    request_data_str: str = Form(
        ..., description="A JSON string representing the full analysis request."
    ),
) -> schemas.AnalysisRequest:
    """
    A dependency that parses and validates the JSON string from the form data.
    """
    try:
        request_data_dict = json.loads(request_data_str)
        return schemas.AnalysisRequest.model_validate(request_data_dict)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=422, detail="Invalid JSON format in request_data_str."
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=422, detail=f"Validation error in request data: {e}"
        )


# --- ENDPOINT ---


@router.get("/definitions.txt", response_class=PlainTextResponse)
def download_definitions() -> str:
    """
    Returns a plain-text reference of all supported analyses and statistical terms.
    """
    return get_all_definitions_as_text()


@router.post("/headers")
async def extract_headers(file: UploadFile = File(...)):
    """
    Extract column headers from an uploaded CSV or Excel file.
    Returns:
        {"headers": ["col_a", "col_b", ...]}
    """
    filename = file.filename or ""

    try:
        raw = await file.read()
        buffer = BytesIO(raw)

        lowered = filename.lower()
        if lowered.endswith(".csv"):
            df = pd.read_csv(buffer, nrows=0)
        elif lowered.endswith((".xls", ".xlsx")):
            df = pd.read_excel(buffer, nrows=0)
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Please upload CSV or Excel.",
            )

        headers = [str(col) for col in df.columns.tolist()]
        if not headers:
            raise HTTPException(status_code=400, detail="No headers found in file.")

        return {"headers": headers}

    except HTTPException:
        raise
    except Exception as exc:
        # You can log exc here
        raise HTTPException(
            status_code=500, detail="Failed to parse headers from file."
        )


@router.post("/generate-report/", tags=["Reports"], response_class=StreamingResponse)
async def generate_report_endpoint(
    input_file: UploadFile = File(..., description="The source CSV or Excel file."),
    request_data: schemas.AnalysisRequest = Depends(get_analysis_request),
):
    """
    Accepts a data file and a JSON analysis request, then returns a ZIP file
    containing up to two CSVs:

      - report.csv   -> main analysis blocks (custom, summary_stats, etc.)
      - insights.csv -> any Crosstab and Correlation analysis blocks
    """
    try:
        input_df = load_tabular_data(input_file.file, input_file.filename)

        blocks = list(run_dynamic_analysis(input_df, request_data))

        report_blocks: list[schemas.ReportBlock] = []
        insight_blocks: list[schemas.ReportBlock] = []

        for block in blocks:
            title_lower = block.title.lower()

            if (
                "correlation" in title_lower
                or "crosstab" in title_lower
                or "cross-tab" in title_lower
            ):
                insight_blocks.append(block)
            else:
                report_blocks.append(block)

        report_csv = _render_category(report_blocks)
        insights_csv = _render_insights(insight_blocks)

        # Build ZIP in memory.
        zip_buf = BytesIO()
        with zipfile.ZipFile(zip_buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            if report_csv:
                zf.writestr("report.csv", report_csv)
            if insights_csv:
                zf.writestr("insights.csv", insights_csv)

        zip_buf.seek(0)

        # Derive zip filename from requested output_filename.
        out_name = request_data.output_filename or "generated_report.zip"
        if not out_name.lower().endswith(".zip"):
            if "." in out_name:
                out_name = out_name.rsplit(".", 1)[0]
            out_name = f"{out_name}.zip"

        return StreamingResponse(
            zip_buf,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{out_name}"'},
        )
    except Exception as e:
        logging.exception("Error in generate_report_endpoint")
        return Response(
            content=json.dumps(
                {
                    "detail": "An unexpected internal error occurred.",
                    "error": str(e),
                }
            ),
            status_code=500,
            media_type="application/json",
        )
