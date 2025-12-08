# tests/test_summary_stats.py

import pytest
import pandas as pd
import numpy as np

# Import the specific function and schemas we are testing
from backend.app.analysis.summary_stats import run
from backend.app.schemas import (
    SummaryStatsAnalysis,
    Filter,
    ReportBlock,
    ColumnTransformation,
    Transformation,
)


# Use a pytest fixture for clean, reusable test data.
@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Provides a standard DataFrame for testing summary stats."""
    data = {
        "region": ["NA", "NA", "EU", "EU", "NA", "EU"],
        "product": ["A", "B", "A", "B", "A", "B"],
        "sales": [100, 200, 50, 150, 150, 250],
        "units": [10, 20, 5, 15, 15, 25],
        "customer_name": ["Cust1", "Cust2", "Cust3", "Cust4", "Cust5", "Cust6"],
        "tags": ["fast, cheap", "slow", "fast", "slow, cheap", "fast", "slow"],
    }
    return pd.DataFrame(data)


# ==============================================================================
# 1. Basic Functionality Tests
# ==============================================================================


def test_summary_stats_no_grouping(sample_df):
    """Tests calculating stats for the entire DataFrame without grouping."""
    step = SummaryStatsAnalysis(
        output_name="Overall Stats", numeric_columns=["sales", "units"]
    )
    result = run(sample_df, step)

    # Assert on the structure and metadata
    assert isinstance(result, ReportBlock)
    assert result.title == "Overall Stats"

    results_df = result.data

    # Test the mean of 'sales'
    # Overall sales mean: (100+200+50+150+150+250)/6 = 900/6 = 150.0
    sales_mean = results_df.loc[
        (results_df["Column"] == "sales") & (results_df["Metric"] == "mean"), "Value"
    ].iloc[0]
    assert sales_mean == pytest.approx(150.0)

    # Test the count of 'units'
    units_count = results_df.loc[
        (results_df["Column"] == "units") & (results_df["Metric"] == "count"), "Value"
    ].iloc[0]
    assert units_count == 6


def test_summary_stats_single_group(sample_df):
    """Tests grouping by a single categorical column ('region')."""
    step = SummaryStatsAnalysis(
        output_name="Regional Stats", group_by=["region"], numeric_columns=["sales"]
    )
    result = run(sample_df, step)
    results_df = result.data

    # Test the 'NA' group mean
    # NA sales: [100, 200, 150]. Mean = 450 / 3 = 150.0
    na_sales_mean = results_df.loc[
        (results_df["Group"] == "NA") & (results_df["Metric"] == "mean"), "Value"
    ].iloc[0]
    assert na_sales_mean == pytest.approx(150.0)

    # Test the 'EU' group mean
    # EU sales: [50, 150, 250]. Mean = 450 / 3 = 150.0
    eu_sales_mean = results_df.loc[
        (results_df["Group"] == "EU") & (results_df["Metric"] == "mean"), "Value"
    ].iloc[0]
    assert eu_sales_mean == pytest.approx(150.0)


def test_summary_stats_multi_group(sample_df):
    """Tests grouping by multiple columns ('region' and 'product')."""
    step = SummaryStatsAnalysis(
        output_name="Detailed Stats",
        group_by=["region", "product"],
        numeric_columns=["sales"],
    )
    result = run(sample_df, step)
    results_df = result.data

    # Test a specific multi-group
    # Mean sales for NA, Product A: (100 + 150) / 2 = 125.00
    na_a_mean = results_df.loc[
        (results_df["Group"] == "NA, A") & (results_df["Metric"] == "mean"), "Value"
    ].iloc[0]
    assert na_a_mean == pytest.approx(125.0)


# ==============================================================================
# 2. Interaction Tests (Filters, Transformations)
# ==============================================================================


def test_summary_stats_with_filter(sample_df):
    """Tests that pre-analysis filters are correctly applied."""
    step = SummaryStatsAnalysis(
        output_name="Product B Stats",
        filters=[Filter(column="product", operator="eq", value="B")],
        numeric_columns=["sales"],
    )
    result = run(sample_df, step)
    results_df = result.data

    # Only rows for product 'B' should be included: [200, 150, 250]
    # Mean: (200 + 150 + 250) / 3 = 600 / 3 = 200.00
    sales_mean = results_df.loc[
        (results_df["Group"] == "Full Dataset") & (results_df["Metric"] == "mean"),
        "Value",
    ].iloc[0]
    assert sales_mean == pytest.approx(200.0)


def test_summary_stats_with_transformation(sample_df):
    """Tests that stats can be calculated after a transformation on a different column."""
    step = SummaryStatsAnalysis(
        output_name="Tag Stats",
        # We want stats on 'units'
        numeric_columns=["units"],
        # But we apply a transformation to the 'tags' column
        column_transformations=[
            ColumnTransformation(
                column_name="tags",
                transformations=[
                    Transformation(
                        action="split_and_explode", params={"delimiter": ","}
                    )
                ],
            )
        ],
    )
    result = run(sample_df, step)
    results_df = result.data

    # The transformation on 'tags' should not affect the stats of 'units'.
    # The mean of units is (10+20+5+15+15+25)/6 = 90/6 = 15.0
    units_mean = results_df.loc[
        (results_df["Column"] == "units") & (results_df["Metric"] == "mean"), "Value"
    ].iloc[0]
    assert units_mean == pytest.approx(15.0)


# ==============================================================================
# 3. Edge Case Tests
# ==============================================================================


def test_summary_stats_ignores_non_numeric_column(sample_df):
    """Tests that a non-numeric column is gracefully ignored."""
    step = SummaryStatsAnalysis(
        output_name="Mixed Columns",
        numeric_columns=["sales", "customer_name"],  # customer_name is not numeric
    )
    result = run(sample_df, step)
    results_df = result.data

    # The result should only contain stats for 'sales'.
    assert "customer_name" not in results_df["Column"].unique()
    assert "sales" in results_df["Column"].unique()


def test_summary_stats_empty_input_df():
    """Tests that the function returns an empty but correctly structured result for an empty DataFrame."""
    empty_df = pd.DataFrame({"sales": [], "units": []})
    step = SummaryStatsAnalysis(output_name="Empty DF Test", numeric_columns=["sales"])
    result = run(empty_df, step)

    assert isinstance(result, ReportBlock)
    assert result.data.empty
    # Check that the empty dataframe still has the correct columns
    assert list(result.data.columns) == ["Group", "Column", "Metric", "Value"]


def test_summary_stats_filter_yields_no_rows(sample_df):
    """Tests graceful handling when a filter results in an empty DataFrame."""
    step = SummaryStatsAnalysis(
        output_name="No Match Test",
        filters=[
            Filter(column="region", operator="eq", value="ASIA")
        ],  # No ASIA region
        numeric_columns=["sales"],
    )
    result = run(sample_df, step)

    assert isinstance(result, ReportBlock)
    assert result.data.empty
