from datetime import datetime, timezone
from sqlalchemy import select
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse, Response, PlainTextResponse
from utils.definitions import get_all_definitions_as_text
from pydantic import ValidationError
import json
import urllib.parse
import pandas as pd
import logging
from io import BytesIO
import zipfile

import schemas
from extract import load_tabular_data
from orchestrator import run_dynamic_analysis
from generator import to_csv_string
from database import get_db
from models import ReportRun, RunStepResult, RunArtifact
from sqlalchemy.orm import Session, selectinload

router = APIRouter()

# 50 MB — large enough for real-world CSVs, small enough to prevent DoS.
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


@router.get("/runs/", tags=["Reports"])
def list_report_runs(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """
    Return a lightweight run-history view so persistence can be inspected
    from the API without touching the database directly.

    Paginate with `limit` (max 200) and `offset`.
    """
    limit = min(limit, 200)
    stmt = select(ReportRun).order_by(ReportRun.created_at.desc()).limit(limit).offset(offset)
    runs = db.execute(stmt).scalars().all()

    return [
        {
            "id": run.id,
            "status": run.status,
            "input_filename": run.input_filename,
            "output_filename": run.output_filename,
            "total_steps": run.total_steps,
            "completed_steps": run.completed_steps,
            "error_message": run.error_message,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "input_row_count": run.input_row_count,
            "input_column_count": run.input_column_count,
            "duration_seconds": run.duration_seconds,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "updated_at": run.updated_at.isoformat() if run.updated_at else None,
        }
        for run in runs
    ]

@router.get("/runs/{run_id}", tags=["Reports"])
def get_report_run(run_id: str, db: Session = Depends(get_db)):
    """
    Return a single run with its step results and generated artifacts so a
    caller can inspect exactly what happened for that run.
    """
    stmt = (
        select(ReportRun)
        .options(
            selectinload(ReportRun.step_results),
            selectinload(ReportRun.artifacts),
        )
        .where(ReportRun.id == run_id)
    )
    run = db.execute(stmt).scalars().first()

    if run is None:
        raise HTTPException(status_code=404, detail="Run not found.")

    step_results = sorted(run.step_results, key=lambda item: item.step_index)
    artifacts = sorted(run.artifacts, key=lambda item: item.created_at)

    return {
        "id": run.id,
        "status": run.status,
        "input_filename": run.input_filename,
        "output_filename": run.output_filename,
        "request_payload": run.request_payload,
        "total_steps": run.total_steps,
        "completed_steps": run.completed_steps,
        "error_message": run.error_message,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "input_row_count": run.input_row_count,
        "input_column_count": run.input_column_count,
        "duration_seconds": run.duration_seconds,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "updated_at": run.updated_at.isoformat() if run.updated_at else None,
        "steps": [
            {
                "id": step.id,
                "step_index": step.step_index,
                "step_type": step.step_type,
                "output_name": step.output_name,
                "status": step.status,
                "row_count": step.row_count,
                "error_message": step.error_message,
                "started_at": step.started_at.isoformat() if step.started_at else None,
                "finished_at": step.finished_at.isoformat() if step.finished_at else None,
                "created_at": step.created_at.isoformat() if step.created_at else None,
                "duration_seconds": step.duration_seconds,
            }
            for step in step_results
        ],
        "artifacts": [
            {
                "id": artifact.id,
                "artifact_type": artifact.artifact_type,
                "file_name": artifact.file_name,
                "file_path": artifact.file_path,
                "content_type": artifact.content_type,
                "size_bytes": artifact.size_bytes,
                "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
            }
            for artifact in artifacts
        ],
    }

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


# Column signatures produced by each compact-format analysis operation.
# Defined here so that a rename in an analysis module surfaces as a single
# point-of-change rather than a silent rendering regression.
_COLS_DISTRIBUTION = ["", "%", "Count"]
_COLS_DUPLICATE = ["Duplicates", "Instances"]
_COLS_AVERAGE = ["Average"]
_COLS_SUM = ["Sum"]
_COLS_MEDIAN = ["Median"]


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
        if cols == _COLS_DISTRIBUTION:
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

        elif cols == _COLS_DUPLICATE:
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

        elif cols in (_COLS_AVERAGE, _COLS_SUM, _COLS_MEDIAN):
            metric_label = cols[0]
            rows.append([f"{hdr} — {op_label}", "", metric_label])
            for _, row in data.iterrows():
                rows.append(["", "", str(row[metric_label])])

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


def _build_run_scoped_filename(filename: str, run_id: str) -> str:
    """
    Append the run id to a filename so generated artifacts can be traced
    back to the exact ReportRun that created them.
    """
    if "." in filename:
        stem, ext = filename.rsplit(".", 1)
        return f"{stem}__{run_id}.{ext}"
    return f"{filename}__{run_id}"


def _build_export_title_csv(output_filename: str, run_id: str) -> str:
    """
    Build a top-of-sheet metadata row so the generated spreadsheet clearly shows
    the logical output title and the run id that produced it.
    """
    base_title = output_filename or "generated_report"
    if "." in base_title:
        base_title = base_title.rsplit(".", 1)[0]

    # Clean it up for display.
    display_title = base_title.replace("_", " ").strip()

    title_df = pd.DataFrame([[display_title, f"Run ID: {run_id}"]])
    return to_csv_string(title_df, header=False) + "\n"


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

        if len(raw) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum allowed size is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
            )

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
    except Exception:
        logging.exception("Failed to extract headers from uploaded file.")
        raise HTTPException(
            status_code=500, detail="Failed to parse headers from file."
        )


@router.post("/generate-report/", tags=["Reports"], response_class=StreamingResponse)
async def generate_report_endpoint(
    input_file: UploadFile = File(..., description="The source CSV or Excel file."),
    request_data: schemas.AnalysisRequest = Depends(get_analysis_request),
    db: Session = Depends(get_db),
):
    """
    Accepts a data file and a JSON analysis request, then returns a ZIP file
    containing up to two CSVs:

      - report.csv   -> main analysis blocks (custom, summary_stats, etc.)
      - insights.csv -> any Crosstab and Correlation analysis blocks
    """
    run = ReportRun(
        status="running",
        input_filename=input_file.filename,
        output_filename=request_data.output_filename,
        request_payload=request_data.model_dump(mode="json"),
        total_steps=len(request_data.analysis_steps),
        completed_steps=0,
        started_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        raw_bytes = await input_file.read()
        if len(raw_bytes) > MAX_UPLOAD_BYTES:
            run.status = "failed"
            run.error_message = "Uploaded file exceeds maximum allowed size."
            run.finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.commit()
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum allowed size is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
            )

        input_df = load_tabular_data(BytesIO(raw_bytes), input_file.filename)
        run.input_row_count = len(input_df.index)
        run.input_column_count = len(input_df.columns)

        report_blocks: list[schemas.ReportBlock] = []
        insight_blocks: list[schemas.ReportBlock] = []
        completed_steps = 0

        for index, block in enumerate(run_dynamic_analysis(input_df, request_data), start=1):
            step_finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
            title_lower = block.title.lower()
            step = request_data.analysis_steps[index - 1]
            is_error_block = title_lower.startswith("error in step:")

            if (
                "correlation" in title_lower
                or "crosstab" in title_lower
                or "cross-tab" in title_lower
            ):
                insight_blocks.append(block)
            else:
                report_blocks.append(block)

            row_count = None
            if block.data is not None:
                row_count = len(block.data.index)

            step_result = RunStepResult(
                run_id=run.id,
                step_index=index,
                step_type=step.type,
                output_name=step.output_name,
                status="failed" if is_error_block else "success",
                row_count=row_count,
                error_message=(
                    "Step returned an error block during analysis execution."
                    if is_error_block
                    else None
                ),
                started_at=run.started_at,
                finished_at=step_finished_at,
                duration_seconds=(
                    (step_finished_at - run.started_at).total_seconds()
                    if run.started_at
                    else None
                ),
            )
            db.add(step_result)
            completed_steps += 1

        report_body = _render_category(report_blocks)
        insights_body = _render_insights(insight_blocks)

        report_csv = ""
        if report_body:
            report_csv = (
                _build_export_title_csv(
                    request_data.output_filename or "generated_report",
                    run.id,
                )
                + report_body
            )

        insights_csv = ""
        if insights_body:
            insights_csv = (
                _build_export_title_csv(
                    f"{(request_data.output_filename or 'generated_report')}_insights",
                    run.id,
                )
                + insights_body
            )
        

        report_csv_name = _build_run_scoped_filename("report.csv", run.id)
        insights_csv_name = _build_run_scoped_filename("insights.csv", run.id)

        # Build ZIP in memory.
        zip_buf = BytesIO()
        with zipfile.ZipFile(zip_buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            if report_csv:
                zf.writestr(report_csv_name, report_csv)
                db.add(
                    RunArtifact(
                        run_id=run.id,
                        artifact_type="report_csv",
                        file_name=report_csv_name,
                        file_path=None,
                        content_type="text/csv",
                        size_bytes=len(report_csv.encode("utf-8")),
                    )
                )
            if insights_csv:
                zf.writestr(insights_csv_name, insights_csv)
                db.add(
                    RunArtifact(
                        run_id=run.id,
                        artifact_type="insights_csv",
                        file_name=insights_csv_name,
                        file_path=None,
                        content_type="text/csv",
                        size_bytes=len(insights_csv.encode("utf-8")),
                    )
                )

        zip_buf.seek(0)
        zip_bytes = zip_buf.getvalue()

        # Derive zip filename from requested output_filename and scope it to the run id.
        out_name = request_data.output_filename or "generated_report.zip"
        if not out_name.lower().endswith(".zip"):
            if "." in out_name:
                out_name = out_name.rsplit(".", 1)[0]
            out_name = f"{out_name}.zip"
        
        out_name = _build_run_scoped_filename(out_name, run.id)

        db.add(
            RunArtifact(
                run_id=run.id,
                artifact_type="zip",
                file_name=out_name,
                file_path=None,
                content_type="application/zip",
                size_bytes=len(zip_bytes),
            )
        )

        run.status = "success"
        run.completed_steps = completed_steps
        run.finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
        run.duration_seconds = (
            (run.finished_at - run.started_at).total_seconds()
            if run.started_at and run.finished_at
            else None
        )
        run.output_filename = out_name
        db.commit()

        zip_buf = BytesIO(zip_bytes)
        return StreamingResponse(
            zip_buf,
            media_type="application/zip",
            headers={
                "Content-Disposition": (
                f'attachment; filename="{out_name.encode("ascii", errors="replace").decode()}";'
                f" filename*=UTF-8''{urllib.parse.quote(out_name)}"
            ),
                "X-Report-Run-Id": run.id,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        run.status = "failed"
        run.error_message = str(e)
        run.finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()

        logging.exception("Error in generate_report_endpoint")
        return Response(
            content=json.dumps({"detail": "An unexpected internal error occurred."}),
            status_code=500,
            media_type="application/json",
        )
