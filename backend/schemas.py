
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Union, Annotated
import pandas as pd
from pydantic import ConfigDict

"""
---------------------
SCHEMA.PY
---------------------
Holds the Class definitions for the various analysis models, specifying input structure, data type, available filters, etc.
NOTE: For frontend purposes, the JSON request the backend receives should adhere to the structure dictated by the Schemas. If the frontend 
sends back key_driver_analysis instead of key_driver for the analysis type, it will result in an error. 
"""

# --- CORE DEFINITIONS ---


# A filter is always structured as:
# {"column": "column_name", "operator": "operator_name", "value": "some_value"}
class Filter(BaseModel):
    """Defines a rule to filter data BEFORE an analysis runs."""

    column: str
    operator: Literal["eq", "neq", "gt", "lt", "in", "not_in", "contains"]
    value: Union[str, int, float, List[str], List[int], List[float]]


# These actions are used within a `Transformation` object to manipulate the
# data in a column *before* the final analysis operation is performed.
TransformationAction = Literal[
    "split_and_explode", "to_root_node", "strip_whitespace", "to_numeric", "fill_na"
]


class Transformation(BaseModel):
    """A generic transformation model for the 'CustomAnalysis' workbench."""

    action: TransformationAction
    params: Dict[str, Any] = Field(default_factory=dict)


class ColumnTransformation(BaseModel):
    """A model to associate a list of transformations with a specific column."""

    column_name: str
    transformations: List[Transformation]


# These operations are the final calculation step in a "CustomAnalysis".
AnalysisOperation = Literal[
    "average", "sum", "median", "duplicate_count", "distribution", "list_unique_values"
]


# --- BASE MODEL FOR ALL ANALYSIS TYPES ---
class BaseAnalysis(BaseModel):
    output_name: str
    filters: List[Filter] = Field(default_factory=list)
    group_by: List[str] = Field(default_factory=list)


# --- HIGH-LEVEL ANALYSIS TYPE DEFINITIONS ---


class CustomAnalysis(BaseAnalysis):
    type: Literal["custom"] = "custom"
    target_columns: Annotated[List[str], Field(min_length=1)]
    transformations: List[Transformation]  # Uses the generic model
    operation: AnalysisOperation
    post_transformation_filters: List[Filter] = Field(default_factory=list)


class SummaryStatsAnalysis(BaseAnalysis):
    type: Literal["summary_stats"] = "summary_stats"
    numeric_columns: Annotated[List[str], Field(min_length=1)]
    # Expects a list of objects, each specifying a column and its transformations.
    column_transformations: List[ColumnTransformation] = Field(default_factory=list)


class CrosstabAnalysis(BaseAnalysis):
    type: Literal["crosstab"] = "crosstab"
    index_column: str
    column_to_compare: str
    column_transformations: List[ColumnTransformation] = Field(default_factory=list)
    show_percentages: Literal["none", "index", "columns", "all"] = "none"


class OutlierDetectionAnalysis(BaseAnalysis):
    type: Literal["outlier_detection"] = "outlier_detection"
    target_columns: Annotated[List[str], Field(min_length=1)]
    method: Literal["iqr", "z-score"] = "iqr"
    threshold: float = Field(1.5, gt=0)


class KeyDriverAnalysis(BaseAnalysis):
    type: Literal["key_driver"] = "key_driver"
    target_variable: str
    feature_columns: Annotated[List[str], Field(min_length=1)]

    # --- NEW: MUST-HAVE ---
    # Explicitly define which features are categorical and need to be one-hot encoded.
    categorical_features: List[str] = Field(
        default_factory=list,
        description="List of feature columns that should be treated as categorical (will be one-hot encoded).",
    )

    # --- NEW: NICE-TO-HAVE ---
    # Allow the user to filter results based on statistical significance.
    p_value_threshold: float = Field(
        default=0.05,
        gt=0,
        le=1,
        description="P-value threshold for a feature to be considered a 'significant' driver.",
    )

    # --- NEW: POWER-USER FEATURE ---
    # Control whether the model calculates a constant (intercept).
    include_intercept: bool = Field(
        default=True,
        description="Whether to include a constant (intercept) term in the regression model.",
    )


class TimeSeriesAnalysis(BaseAnalysis):
    type: Literal["time_series"] = "time_series"
    metric_column: str
    metric: Literal["sum", "average", "count"]
    date_column: str
    frequency: Literal["D", "W", "ME", "QE", "YE"]


class CorrelationAnalysis(BaseAnalysis):
    type: Literal["correlation"] = "correlation"
    columns: Annotated[List[str], Field(min_length=2)]  # Corrected syntax
    threshold: float = Field(0.2)


# --- THE MAIN REQUEST BODY ---
AnalysisJob = Union[
    CustomAnalysis,
    SummaryStatsAnalysis,
    CrosstabAnalysis,
    OutlierDetectionAnalysis,
    KeyDriverAnalysis,
    TimeSeriesAnalysis,
    CorrelationAnalysis,
]


class AnalysisRequest(BaseModel):
    """The main request body for a flexible analysis job."""

    output_filename: str = Field(
        "generated_report.csv", description="The desired name for the output file."
    )
    analysis_steps: List[AnalysisJob]


class ReportBlock(BaseModel):
    """
    A structured data contract for a single block of analysis results.
    This replaces the ambiguous 'List[List[Any]]'.
    """

    # tells Pydantic it's okay to have a complex type like a DataFrame inside a model.
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # The user-defined title for this analysis block.
    title: str

    # The actual data, as a clean pandas DataFrame. No presentation, just raw results.
    data: pd.DataFrame
