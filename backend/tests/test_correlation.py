# tests/test_correlation.py

import pytest
import pandas as pd
import numpy as np

# Import the function and schemas to be tested
from backend.app.analysis.correlation import run
from backend.app.schemas import CorrelationAnalysis, Filter, ReportBlock


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Provides a DataFrame with numeric and categorical data for correlation testing."""
    data = {
        "region": ["NA", "NA", "EU", "EU", "NA", "EU"],
        "product": ["A", "B", "A", "B", "A", "B"],
        # sales and units are strongly positively correlated
        "sales": [100, 200, 50, 150, 110, 210],
        "units": [10, 20, 5, 15, 11, 21],
        # rating is perfectly correlated with product
        "rating": ["good", "bad", "good", "bad", "good", "bad"],
    }
    return pd.DataFrame(data)


# ==============================================================================
# 1. Basic Functionality Tests
# ==============================================================================


def test_correlation_pearson_numeric(sample_df):
    """Tests a standard Pearson correlation between two numeric columns."""
    step = CorrelationAnalysis(
        output_name="Sales vs Units",
        columns=["sales", "units"],
        threshold=0.1,  # Low threshold to ensure we get a result
    )
    result = run(sample_df, step)

    assert isinstance(result, ReportBlock)
    results_df = result.data

    # Expected: one row of results for the full dataset
    assert len(results_df) == 1

    record = results_df.iloc[0]
    assert record["Group"] == "Full Dataset"
    assert record["Correlation Type"] == "Pearson"
    # Calculate the expected correlation
    expected_corr = sample_df["sales"].corr(sample_df["units"])
    assert record["Correlation Value"] == pytest.approx(expected_corr)
    assert record["Correlation Value"] > 0.95  # Sanity check for strong correlation


def test_correlation_cramers_v_categorical(sample_df):
    """Tests a Cramér's V correlation between two categorical columns."""
    step = CorrelationAnalysis(
        output_name="Product vs Rating", columns=["product", "rating"], threshold=0.1
    )
    result = run(sample_df, step)

    assert isinstance(result, ReportBlock)
    results_df = result.data

    # Expected: one row of results, perfect correlation
    assert len(results_df) == 1
    record = results_df.iloc[0]
    assert record["Correlation Type"] == "Cramér's V"
    # 'product' and 'rating' are perfectly associated in the fixture
    assert record["Correlation Value"] == pytest.approx(1.0)


def test_correlation_mixed_type(sample_df):
    """Tests that mixed numeric/categorical pairs are handled correctly."""
    step = CorrelationAnalysis(
        output_name="Sales vs Product", columns=["sales", "product"]
    )
    result = run(sample_df, step)
    results_df = result.data

    assert len(results_df) == 1
    record = results_df.iloc[0]
    assert record["Correlation Type"] == "Mixed"
    # The value for a non-calculable mixed type should be NaN
    assert pd.isna(record["Correlation Value"])


# ==============================================================================
# 2. Interaction and Parameter Tests
# ==============================================================================


def test_correlation_threshold_filters_out_result(sample_df):
    """Tests that the threshold correctly filters out correlations that are too weak."""
    step = CorrelationAnalysis(
        output_name="High Threshold Test",
        columns=["sales", "units"],
        threshold=1.1,  # Set threshold higher than the actual correlation
    )
    result = run(sample_df, step)

    # The correlation exists but is below the threshold, so the result should be empty.
    assert result.data.empty


def test_correlation_with_grouping(sample_df):
    """Tests that correlation is calculated correctly for each group."""
    step = CorrelationAnalysis(
        output_name="Grouped Correlation",
        columns=["sales", "units"],
        group_by=["product"],
    )
    result = run(sample_df, step)
    results_df = result.data

    # We expect two results, one for product 'A' and one for 'B'
    assert len(results_df) == 2

    # Test Group 'A'
    group_a_corr = results_df.loc[results_df["Group"] == "A", "Correlation Value"].iloc[
        0
    ]
    df_a = sample_df[sample_df["product"] == "A"]
    expected_a_corr = df_a["sales"].corr(df_a["units"])
    assert group_a_corr == pytest.approx(expected_a_corr)

    # Test Group 'B'
    group_b_corr = results_df.loc[results_df["Group"] == "B", "Correlation Value"].iloc[
        0
    ]
    df_b = sample_df[sample_df["product"] == "B"]
    expected_b_corr = df_b["sales"].corr(df_b["units"])
    assert group_b_corr == pytest.approx(expected_b_corr)


def test_correlation_with_filtering(sample_df):
    """Tests that filtering is applied before correlation is calculated."""
    step = CorrelationAnalysis(
        output_name="NA Region Correlation",
        columns=["sales", "units"],
        filters=[Filter(column="region", operator="eq", value="NA")],
    )
    result = run(sample_df, step)
    results_df = result.data

    # We expect only one result, calculated on the filtered 'NA' data
    assert len(results_df) == 1

    record = results_df.iloc[0]
    assert record["Group"] == "Full Dataset"  # No grouping was applied

    # Calculate expected correlation only on the filtered data
    df_na = sample_df[sample_df["region"] == "NA"]
    expected_corr = df_na["sales"].corr(df_na["units"])
    assert record["Correlation Value"] == pytest.approx(expected_corr)


# ==============================================================================
# 3. Edge Case Tests
# ==============================================================================


def test_correlation_no_overlapping_data():
    """Tests the case where aligned data is empty, resulting in no correlation."""
    df = pd.DataFrame({"a": [1, 2, np.nan, np.nan], "b": [np.nan, np.nan, 3, 4]})
    step = CorrelationAnalysis(output_name="No Overlap", columns=["a", "b"])
    result = run(df, step)

    # No overlapping data after dropping NaNs and aligning, so the result should be empty.
    assert result.data.empty
