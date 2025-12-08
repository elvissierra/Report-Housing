# tests/test_key_driver.py

import pytest
import pandas as pd
import numpy as np

# Import the function and schemas to be tested
from backend.app.analysis.key_driver import run
from backend.app.schemas import KeyDriverAnalysis, Filter, ReportBlock


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Provides a DataFrame for testing linear regression."""
    # In this data:
    # - 'sales' is the target.
    # - 'marketing_spend' is a strong positive driver.
    # - 'website_visits' is a weak, non-significant driver.
    # - 'region' is a categorical driver.
    data = {
        "sales": [150, 250, 220, 350, 400, 500, 160, 260],
        "marketing_spend": [10, 20, 18, 30, 35, 45, 12, 22],
        "website_visits": [100, 120, 110, 130, 125, 140, 105, 122],
        "region": ["NA", "NA", "NA", "NA", "EU", "EU", "EU", "EU"],
    }
    return pd.DataFrame(data)


# ==============================================================================
# 1. Basic Functionality Tests
# ==============================================================================


def test_key_driver_basic_numeric(sample_df):
    """Tests a simple regression with only numeric features."""
    step = KeyDriverAnalysis(
        output_name="Basic Drivers of Sales",
        target_variable="sales",
        feature_columns=["marketing_spend", "website_visits"],
    )
    result = run(sample_df, step)

    assert isinstance(result, ReportBlock)
    results_df = result.data.set_index("Feature")

    # Check for R-squared value
    assert "R-squared" in results_df.index
    assert results_df.loc["R-squared", "Coefficient"] > 0.9  # Expect a good fit

    # Check marketing_spend (strong driver)
    assert results_df.loc["marketing_spend", "P-value"] < 0.05  # Should be significant
    assert results_df.loc["marketing_spend", "Coefficient"] > 0  # Should be positive

    # Check website_visits (weak driver)
    # Note: Depending on the data, this might sometimes be significant.
    # A better test is to check that its coefficient is much smaller.
    # assert abs(results_df.loc['website_visits', 'Coefficient']) < abs(results_df.loc['marketing_spend', 'Coefficient'])
    assert "website_visits" not in results_df.index


def test_key_driver_with_categorical_feature(sample_df):
    """Tests that categorical features are correctly one-hot encoded."""
    step = KeyDriverAnalysis(
        output_name="Drivers with Region",
        target_variable="sales",
        feature_columns=["marketing_spend", "region"],
        categorical_features=["region"],  # Explicitly declare 'region' as categorical
        # Temporarily disable p-value filtering to test the mechanism itself.
        p_value_threshold=1.0,
    )
    result = run(sample_df, step)
    results_df = result.data

    # The one-hot encoding should create a 'region_NA' column (since 'EU' is dropped as the base).
    # We expect to see this new feature in the results.
    assert "region_NA" in results_df["Feature"].values

    # The original 'region' column should NOT be in the results.
    assert "region" not in results_df["Feature"].values


# ==============================================================================
# 2. Parameter and Interaction Tests
# ==============================================================================


def test_key_driver_p_value_threshold(sample_df):
    """Tests that the p-value threshold correctly filters results."""
    # First, run with a low threshold that should include everything
    step_low_thresh = KeyDriverAnalysis(
        output_name="Low Threshold",
        target_variable="sales",
        feature_columns=["marketing_spend", "website_visits"],
        p_value_threshold=1.0,  # Include all results
    )
    result_low = run(sample_df, step_low_thresh)
    # Should include const, marketing_spend, website_visits, and R-squared
    assert len(result_low.data) == 4

    # Second, run with a high threshold that should only include marketing_spend
    step_high_thresh = KeyDriverAnalysis(
        output_name="High Threshold",
        target_variable="sales",
        feature_columns=["marketing_spend", "website_visits"],
        p_value_threshold=0.05,  # Only statistically significant results
    )
    result_high = run(sample_df, step_high_thresh)
    results_df_high = result_high.data

    # Should include const, marketing_spend, and R-squared, but NOT website_visits
    assert "website_visits" not in results_df_high["Feature"].values
    assert "marketing_spend" in results_df_high["Feature"].values
    assert len(results_df_high) == 3


@pytest.mark.filterwarnings("ignore:omni_normtest is not valid")
def test_key_driver_with_grouping(sample_df):
    """Tests that regression is run independently for each group."""
    step = KeyDriverAnalysis(
        output_name="Regional Drivers",
        target_variable="sales",
        feature_columns=["marketing_spend"],
        group_by=["region"],
    )
    result = run(sample_df, step)
    results_df = result.data

    # We should have results for both 'NA' and 'EU' groups
    assert "NA" in results_df["Group"].unique()
    assert "EU" in results_df["Group"].unique()

    # Each group should have its own R-squared and coefficient results
    assert (
        len(results_df[results_df["Group"] == "NA"]) == 3
    )  # const, marketing_spend, R-squared
    assert len(results_df[results_df["Group"] == "EU"]) == 3


# ==============================================================================
# 3. Edge Case Tests
# ==============================================================================


def test_key_driver_insufficient_data(sample_df):
    """Tests that the analysis is skipped if there's not enough data after cleaning."""
    # Filter down to a very small dataset
    step = KeyDriverAnalysis(
        output_name="Insufficient Data",
        target_variable="sales",
        feature_columns=["marketing_spend", "website_visits"],
        filters=[Filter(column="sales", operator="lt", value=200)],  # Only 2 rows match
    )
    result = run(sample_df, step)

    # The number of rows (2) is not greater than number of features (2) + 1.
    # The analysis should be skipped, resulting in an empty DataFrame.
    assert result.data.empty
