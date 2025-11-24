
"""
API layer for the reporting pipeline.

Exposes HTTP endpoints that orchestrate calls into report_auto.core.pipeline.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import io
import json
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from report_auto.core.pipeline import run_recipe_workflow, run_auto_report

router = APIRouter(prefix="/reports", tags=["reports"])


class RecipeRunRequest(BaseModel):
    """
    Request body for running a report using a JSON recipe and server-side paths.

    This is primarily useful for automation / scripts that can see the same filesystem
    as the backend. The upload-based endpoint is a better fit for browser UIs.
    """

    recipe: Dict[str, Any] = Field(
        ...,
        description="Full recipe.json structure emitted by the Vue Designer.",
    )
    input_path: str = Field(
        ...,
        description="Path to the input CSV/Excel on the backend filesystem.",
    )
    output_path: str = Field(
        ...,
        description="Destination CSV path on the backend filesystem.",
    )
    multi_sheet: bool = Field(
        False,
        description="If true and the input is an Excel workbook, process all sheets.",
    )


class RecipeRunResponse(BaseModel):
    message: str
    output_path: str


@router.post(
    "/run-recipe",
    response_model=RecipeRunResponse,
    summary="Run a report using a JSON recipe and server-side file paths.",
)
async def run_recipe_with_paths(payload: RecipeRunRequest) -> RecipeRunResponse:
    """
    Execute the reporting pipeline given a recipe.json and input/output paths.

    This endpoint delegates to `run_recipe_workflow` and simply returns the final
    output path for confirmation. Any failures will surface as 400-level errors.
    """
    try:
        run_recipe_workflow(
            recipe=payload.recipe,
            input_path=payload.input_path,
            output_path=payload.output_path,
            multi_sheet=payload.multi_sheet,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return RecipeRunResponse(
        message="Report generated successfully.",
        output_path=payload.output_path,
    )


@router.post(
    "/run-recipe-upload",
    summary="Run a report by uploading a data file and recipe.json from the UI.",
)
async def run_recipe_with_upload(
    file: UploadFile = File(..., description="CSV or Excel file to analyze."),
    recipe: str = Form(
        ...,
        description="recipe.json content as a JSON string (from the Vue Designer).",
    ),
    multi_sheet: bool = Form(
        False,
        description="If true and the upload is an Excel workbook, process all sheets.",
    ),
) -> StreamingResponse:
    """
    Execute the reporting pipeline using an uploaded data file and a recipe.json string.

    This is the UI-friendly endpoint:
    - The browser posts a multipart/form-data request containing:
      - `file`: the CSV/Excel to analyze
      - `recipe`: the JSON string exported from the Designer
      - `multi_sheet`: optional flag for workbooks
    - The API runs the pipeline in a temporary directory.
    - Returns a ZIP bundle containing the main report plus insights artifacts (Correlation_Results.csv, Crosstabs_Output.csv).
    """
    try:
        recipe_obj: Dict[str, Any] = json.loads(recipe)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid recipe JSON") from exc

    # Work inside a temporary directory so we do not pollute the backend filesystem.
    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        input_path = tmpdir_path / file.filename
        output_path = tmpdir_path / "report.csv"

        # Persist upload to disk for the existing pipeline to consume.
        data = await file.read()
        input_path.write_bytes(data)

        try:
            run_recipe_workflow(
                recipe=recipe_obj,
                input_path=str(input_path),
                output_path=str(output_path),
                multi_sheet=multi_sheet,
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        if not output_path.exists():
            raise HTTPException(
                status_code=500, detail="Report was not generated as expected."
            )

        # Prepare ZIP bundle with report.csv, Correlation_Results.csv, and Crosstabs_Output.csv
        corr_path = tmpdir_path / "Correlation_Results.csv"
        crosstab_path = tmpdir_path / "Crosstabs_Output.csv"

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(output_path, arcname="report.csv")
            if corr_path.exists():
                zf.write(corr_path, arcname="Correlation_Results.csv")
            if crosstab_path.exists():
                zf.write(crosstab_path, arcname="Crosstabs_Output.csv")
        zip_buffer.seek(0)
        filename = file.filename.rsplit(".", 1)[0] + "_report_bundle.zip"

    # Stream back the ZIP bundle; tempdir has been cleaned up.
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )