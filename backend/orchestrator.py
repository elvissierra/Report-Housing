import pandas as pd
from typing import Generator
import logging

from analysis import operations
import schemas
from analysis import (
    summary_stats,
    crosstab,
    outlier_detection,
    correlation,
    time_series,
    key_driver,
)


logging.basicConfig(level=logging.INFO)

ANALYSIS_HANDLERS = {
    "custom": operations.run,
    "summary_stats": summary_stats.run,
    "crosstab": crosstab.run,
    "outlier_detection": outlier_detection.run,
    "correlation": correlation.run,
    "time_series": time_series.run,
    "key_driver": key_driver.run,
}


def run_dynamic_analysis(
    df: pd.DataFrame, request: schemas.AnalysisRequest
) -> Generator[schemas.ReportBlock, None, None]:
    """
    A generator that calculates and YIELDS each analysis block one by one.
    """
    for step in request.analysis_steps:
        try:
            handler = ANALYSIS_HANDLERS.get(step.type)
            if handler:
                yield handler(df, step)
            else:
                error_df = pd.DataFrame(
                    [{"Error": f"Unknown analysis type: '{step.type}'"}]
                )
                yield schemas.ReportBlock(
                    title=f"Error in step: {step.output_name}", data=error_df
                )

        except Exception as e:
            logging.error(
                f"Error processing step '{step.output_name}': {e}", exc_info=True
            )

            error_df = pd.DataFrame(
                [{"Error": "An unexpected error occurred during this analysis step."}]
            )
            yield schemas.ReportBlock(
                title=f"Error in step: {step.output_name}", data=error_df
            )
