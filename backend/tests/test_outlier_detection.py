# tests/test_outlier_detection.py

import pytest
import pandas as pd
import numpy as np

# Import the function and schemas to be tested
from backend.app.analysis.outlier_detection import run
from backend.app.schemas import OutlierDetectionAnalysis, ReportBlock

@pytest.fixture
def sample_df() -> pd.DataFrame:
    """A single, robust fixture for all outlier detection tests."""
    data = {
        'group':  ['A', 'A', 'A', 'A',  'A', 'B',  'B', 'B', 'B',   'B'],
        'sales':  [-3000, 10, 12, 15, 11, 100, 110, 500, 105, 5000],
        'units':  [1, 2, 1, 3, 2, 10, 11, 12, 10, 11] # This column has no outliers
    }
    return pd.DataFrame(data)

# ==============================================================================
# 1. Basic Functionality Tests
# ==============================================================================

def test_outlier_iqr_finds_extreme_values(sample_df):
    """Tests that IQR finds the two most extreme values in the full dataset."""
    step = OutlierDetectionAnalysis(target_columns=["sales"], method="iqr", threshold=1.5, output_name="OD Test")
    result = run(sample_df, step)
    
    results_df = result.data
    assert len(results_df) == 3
    assert -3000 in results_df['Outlier Value'].values
    assert 5000 in results_df['Outlier Value'].values
    # Check correct indices
    assert 0 in results_df[results_df['Outlier Value'] == -3000]['Original Row Index'].values
    assert 9 in results_df[results_df['Outlier Value'] == 5000]['Original Row Index'].values

def test_outlier_zscore_finds_extreme_values(sample_df):
    """Tests that Z-Score finds the two most extreme values."""
    step = OutlierDetectionAnalysis(target_columns=["sales"], method="z-score", threshold=1.5, output_name="OD Test")
    result = run(sample_df, step)
    
    results_df = result.data
    assert len(results_df) == 2
    assert -3000 in results_df['Outlier Value'].values
    assert 5000 in results_df['Outlier Value'].values

def test_outlier_iqr_no_outliers_found(sample_df):
    """Tests that IQR method finds no outliers in a clean column."""
    step = OutlierDetectionAnalysis(target_columns=["units"], method="iqr", output_name="OD Test")
    result = run(sample_df, step)
    assert result.data.empty

# ==============================================================================
# 2. Interaction and Parameter Tests
# ==============================================================================

def test_outlier_threshold_parameter(sample_df):
    """Tests that a very high threshold finds no outliers in the 'normal' part of the data."""
    # Create a DataFrame without the two most extreme outliers
    normal_data = sample_df[(sample_df['sales'] > -3000) & (sample_df['sales'] < 5000)]
    
    step = OutlierDetectionAnalysis(target_columns=["sales"], method="iqr", threshold=6.0, output_name="OD Test")
    result = run(normal_data, step)
    
    # The value 500 might be an outlier with a normal threshold, but not with a high one. Testing 6.0 threshold to see if passes
    assert result.data.empty

def test_outlier_with_grouping(sample_df):
    """Tests that outliers are detected independently within each group."""
    step = OutlierDetectionAnalysis(target_columns=["sales"], group_by=["group"], method="iqr", output_name="OD Test")
    result = run(sample_df, step)
    results_df = result.data

    assert len(results_df) == 2, "Expected to find one outlier in each group."

    # Isolate results for clarity
    group_a_outliers = results_df[results_df['Group'] == 'A']['Outlier Value'].values
    group_b_outliers = results_df[results_df['Group'] == 'B']['Outlier Value'].values

    assert len(group_a_outliers) == 1
    assert group_a_outliers[0] == -3000

    assert len(group_b_outliers) == 1
    assert group_b_outliers[0] == 5000
# ==============================================================================
# 3. Edge Case Tests
# ==============================================================================

def test_outlier_empty_input_df():
    """Tests graceful handling of an empty DataFrame."""
    empty_df = pd.DataFrame({'sales': [], 'group': []})
    step = OutlierDetectionAnalysis(target_columns=["sales"], output_name="OD Test")
    result = run(empty_df, step)
    
    assert isinstance(result, ReportBlock)
    assert result.data.empty

def test_outlier_non_numeric_column(sample_df):
    """Tests that a non-numeric column is simply ignored."""
    step = OutlierDetectionAnalysis(target_columns=["group"], output_name="OD Test")
    result = run(sample_df, step)
    assert result.data.empty