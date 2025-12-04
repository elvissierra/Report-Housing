# tests/test_time_series.py

import pytest
import pandas as pd
import numpy as np

# Import the function and schemas to be tested
from backend.app.analysis.time_series import run
from backend.app.schemas import TimeSeriesAnalysis, Filter, ReportBlock

@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Provides a DataFrame with time series data for testing."""
    data = {
        'event_date': [
            '2023-01-15', '2023-01-20', # Jan
            '2023-02-10', '2023-02-12', # Feb
            '2023-03-05',               # Mar
            '2023-01-18', '2023-02-15', # For group B
            'not a date', None          # Bad data
        ],
        'region': ['NA', 'NA', 'EU', 'EU', 'NA', 'NA', 'EU', 'NA', 'EU'],
        'sales':  [100, 50, 200, 100, 300, 70, 150, 999, 999],
    }
    return pd.DataFrame(data)

# ==============================================================================
# 1. Basic Functionality Tests
# ==============================================================================

def test_time_series_monthly_sum(sample_df):
    """Tests a simple monthly sum aggregation."""
    step = TimeSeriesAnalysis(
        output_name="Monthly Sales Sum",
        date_column="event_date",
        metric_column="sales",
        metric="sum",
        frequency="ME" # 'ME' stands for Month-End frequency
    )
    result = run(sample_df, step)

    assert isinstance(result, ReportBlock)
    results_df = result.data.set_index('Timestamp') # Set index for easy lookup
    
    # Check total rows (Jan, Feb, Mar)
    assert len(results_df) == 3
    
    # Expected sums:
    # Jan: 100 + 50 + 70 = 220
    # Feb: 200 + 100 + 150 = 450
    # Mar: 300
    # Note: Timestamps are normalized to the end of the month by .resample('M')
    assert results_df.loc['2023-01-31', 'Value'] == 220
    assert results_df.loc['2023-02-28', 'Value'] == 450
    assert results_df.loc['2023-03-31', 'Value'] == 300

def test_time_series_weekly_average(sample_df):
    """Tests a weekly average aggregation."""
    step = TimeSeriesAnalysis(
        output_name="Weekly Sales Average",
        date_column="event_date",
        metric_column="sales",
        metric="average", # 'average' is an alias for 'mean'
        frequency="W" # 'W' stands for Week-End frequency (Sunday)
    )

    result = run(sample_df, step)
    results_df = result.data

    # --- CORRECTED, ROBUST ASSERTION ---
    # Instead of checking the sum or a specific date, let's check the number of non-empty bins
    # and an average from a known bin.
    # The data has events in the week ending Jan 15 and the week ending Jan 22.
    # So we expect two rows in the output.
    assert len(results_df) == 5

    # Check the average for the week ending Jan 22, which contains '2023-01-20' (50) and '2023-01-18' (70)
    # Average = (50 + 70) / 2 = 60
    # The timestamp in the output will be the end of the week.
    results_df = results_df.set_index('Timestamp')
    assert results_df.loc['2023-01-22', 'Value'] == pytest.approx(60.0)

    # Week ending Feb 12 has data from Feb 10 (200) and Feb 12 (100). Avg = 150.
    assert results_df.loc['2023-02-12', 'Value'] == pytest.approx(150.0)


def test_time_series_quarterly_count(sample_df):
    """Tests a quarterly count aggregation."""
    step = TimeSeriesAnalysis(
        output_name="Quarterly Event Count",
        date_column="event_date",
        metric_column="sales", # metric column doesn't matter for 'count'
        metric="count",
        frequency="QE" # 'QE' stands for Quarter-End
    )
    result = run(sample_df, step)
    results_df = result.data.set_index('Timestamp')

    # All valid dates are in Q1 2023. There are 7 valid dates.
    assert len(results_df) == 1
    assert results_df.loc['2023-03-31', 'Value'] == 7

# ==============================================================================
# 2. Interaction and Parameter Tests
# ==============================================================================

def test_time_series_with_grouping(sample_df):
    """Tests that time series is calculated correctly for each group."""
    step = TimeSeriesAnalysis(
        output_name="Regional Monthly Sales",
        date_column="event_date",
        metric_column="sales",
        metric="sum",
        frequency="ME",
        group_by=["region"]
    )
    result = run(sample_df, step)
    results_df = result.data

    # Test NA group
    na_df = results_df[results_df['Group'] == 'NA'].set_index('Timestamp')
    # NA Jan: 100 + 50 + 70 = 220
    # NA Mar: 300
    assert na_df.loc['2023-01-31', 'Value'] == 220
    assert na_df.loc['2023-03-31', 'Value'] == 300
    assert na_df.loc['2023-02-28', 'Value'] == 0

    # Test EU group
    eu_df = results_df[results_df['Group'] == 'EU'].set_index('Timestamp')
    # EU Feb: 200 + 100 + 150 = 450
    assert eu_df.loc['2023-02-28', 'Value'] == 450
    assert '2023-01-31' not in eu_df.index # EU has no sales in Jan

# ==============================================================================
# 3. Edge Case and Data Quality Tests
# ==============================================================================

def test_time_series_handles_bad_data(sample_df):
    """
    Tests that rows with unparseable dates or non-numeric metrics are ignored.
    This is implicitly tested by all other tests, but this makes it explicit.
    """
    step = TimeSeriesAnalysis(
        output_name="Total Count",
        date_column="event_date",
        metric_column="sales",
        metric="count",
        frequency="YE"
    )
    result = run(sample_df, step)
    results_df = result.data

    # The original DataFrame has 9 rows.
    # 1 has 'not a date', 1 has a None date.
    # The 7 valid rows should be counted.
    assert results_df['Value'].iloc[0] == 7

def test_time_series_empty_input_df():
    """Tests graceful handling of an empty DataFrame."""
    empty_df = pd.DataFrame({'event_date': [], 'sales': []})
    step = TimeSeriesAnalysis(
        output_name="Empty Test",
        date_column="event_date",
        metric_column="sales",
        metric="sum",
        frequency="ME"
    )
    result = run(empty_df, step)

    assert isinstance(result, ReportBlock)
    assert result.data.empty
    assert list(result.data.columns) == ["Timestamp", "Value", "Group"]
