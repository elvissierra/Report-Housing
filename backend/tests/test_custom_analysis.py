# tests/test_custom_analysis.py

import pytest
import pandas as pd
import numpy as np

# Import the NEW, refactored helper functions from their correct location
from backend.app.analysis.custom import (
    _op_average,
    _op_duplicate_count,
    _op_distribution,
    _op_list_unique_values,
)

# ==============================================================================
# 1. Tests for _op_average
# ==============================================================================


def test_op_average_simple_case():
    """Tests a simple average calculation."""
    series = pd.Series([10, 20, 30])
    result_df = _op_average(series)
    # Test the actual numeric value
    assert result_df["average"].iloc[0] == pytest.approx(20.0)


def test_op_average_with_nan():
    """Tests that NaNs are correctly ignored."""
    series = pd.Series([10, 20, np.nan])
    result_df = _op_average(series)
    assert result_df["average"].iloc[0] == pytest.approx(15.0)


def test_op_average_all_nan():
    """Tests that a series of only NaNs results in a NaN output."""
    series = pd.Series([np.nan, np.nan, np.nan])
    result_df = _op_average(series)
    # Test for the correct NaN value, not a magic string "N/A"
    assert pd.isna(result_df["average"].iloc[0])


def test_op_average_with_strings():
    """Tests that non-numeric strings are coerced to NaN and ignored."""
    series = pd.Series([10, 20, "hello", 30])
    result_df = _op_average(series)
    assert result_df["average"].iloc[0] == pytest.approx(20.0)


# ==============================================================================
# 2. Tests for _op_duplicate_count
# ==============================================================================


def test_op_duplicate_count_with_duplicates():
    """Tests a series with clear duplicates."""
    series = pd.Series(["apple", "banana", "apple", "cherry", "banana", "apple"])
    result_df = _op_duplicate_count(series)

    # Use pandas boolean indexing for robust lookups. No more brittle list comparisons.
    assert result_df.loc[result_df["Metric"] == "Total Count", "Value"].iloc[0] == 6
    assert result_df.loc[result_df["Metric"] == "Unique Count", "Value"].iloc[0] == 3
    assert result_df.loc[result_df["Metric"] == "Duplicate Count", "Value"].iloc[0] == 3


def test_op_duplicate_count_no_duplicates():
    """Tests a series with all unique values."""
    series = pd.Series(["apple", "banana", "cherry"])
    result_df = _op_duplicate_count(series)

    assert result_df.loc[result_df["Metric"] == "Total Count", "Value"].iloc[0] == 3
    assert result_df.loc[result_df["Metric"] == "Unique Count", "Value"].iloc[0] == 3
    assert result_df.loc[result_df["Metric"] == "Duplicate Count", "Value"].iloc[0] == 0


# ==============================================================================
# 3. Tests for _op_distribution
# ==============================================================================


def test_op_distribution_simple():
    """Tests value count and percentage calculation."""
    series = pd.Series(
        ["a", "b", "a", "a", "c", "b", "a", "d", "d", "d"]
    )  # 4a, 2b, 1c, 3d
    result_df = _op_distribution(series)

    # Set the 'Value' column as the index for easy, readable lookups
    result_df = result_df.set_index("Value")

    # Assert on the actual numeric data, not formatted strings
    assert result_df.loc["a", "Count"] == 4
    assert result_df.loc["a", "Percentage"] == pytest.approx(40.0)

    assert result_df.loc["d", "Count"] == 3
    assert result_df.loc["d", "Percentage"] == pytest.approx(30.0)

    assert result_df.loc["b", "Count"] == 2
    assert result_df.loc["b", "Percentage"] == pytest.approx(20.0)

    assert result_df.loc["c", "Count"] == 1
    assert result_df.loc["c", "Percentage"] == pytest.approx(10.0)

    assert len(result_df) == 4


# ==============================================================================
# 4. Tests for _op_list_unique_values
# ==============================================================================


def test_op_list_unique_values_strings():
    """Tests sorting and finding unique strings."""
    series = pd.Series(["cherry", "apple", "banana", "apple"])
    result_df = _op_list_unique_values(series)
    # Assert on a simple list, not a list of lists
    assert result_df["Unique Value"].tolist() == ["apple", "banana", "cherry"]


def test_op_list_unique_values_numbers():
    """Tests sorting and finding unique numbers."""
    series = pd.Series([100, 20, 5, 20, 100])
    result_df = _op_list_unique_values(series)
    assert result_df["Unique Value"].tolist() == [5, 20, 100]


def test_op_list_unique_values_mixed_types():
    """Tests that mixed types are coerced to string and sorted."""
    series = pd.Series([100, "apple", 20, "banana"])
    result_df = _op_list_unique_values(series)
    # When sorted as strings: '100', '20', 'apple', 'banana'
    assert result_df["Unique Value"].tolist() == ["100", "20", "apple", "banana"]
