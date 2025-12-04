Report Auto API - Backend Documentation

1. Overview

This document specifies the architecture and API for the backend of the Report Auto application. The backend is a self-contained FastAPI server designed to be run locally. Its sole purpose is to receive a data file and a JSON-based analysis request, process the data according to the request in a memory-efficient streaming pipeline, and return the resulting report as a downloadable CSV file.

The primary technologies used are FastAPI, Pydantic, and Pandas.


2. Project Structure

backend/
├── app/
│   ├── __init__.py
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── helpers.py         # Shared helpers (grouping, etc.)
│   │   ├── correlation.py     # Correlation analysis logic
│   │   ├── crosstab.py        # Crosstabulation logic
│   │   ├── custom.py          # Custom operation logic
│   │   ├── key_driver.py      # Key Driver (regression) logic
│   │   ├── outlier_detection.py # Outlier detection logic
│   │   ├── summary_stats.py   # Summary statistics logic
│   │   └── time_series.py     # Time series analysis logic
│   ├── routers/
│   │   ├── __init__.py
│   │   └── reports.py         # Defines the API endpoint
│   ├── extract.py             # The "Strong Border" for data ingestion
│   ├── generator.py           # Low-level CSV conversion helpers
│   ├── main.py                # Main application entry point (serves UI and API)
│   ├── orchestrator.py        # Dispatches jobs to the analysis modules
│   └── schemas.py             # The application's source of truth for all data structures


── tests/
    ├── __init__.py
    └── test_*.py               # Unit tests for each analysis module. (Exists in root directory)

3. API Endpoint Specification

The backend exposes a single primary endpoint for generating reports.

Endpoint: POST /api/generate-report/
Content-Type: multipart/form-data

Request Parts

The request must contain two parts:

input_file: The raw data file (.csv, .xlsx, .xls).
request_data_str: A URL-encoded JSON string that conforms to the schemas.AnalysisRequest model.

request_data_str JSON Structure Example

This JSON string defines the entire analysis pipeline.

{
  "output_filename": "my_analysis_report.csv",
  "analysis_steps": [
    {
      "type": "summary_stats",
      "output_name": "Overall Sales and Units Summary",
      "numeric_columns": ["sales", "units"],
      "group_by": ["region"]
    },
    {
      "type": "key_driver_analysis",
      "output_name": "Key Drivers of Sales",
      "target_variable": "sales",
      "feature_columns": ["marketing_spend", "website_visits", "product_category"],
      "categorical_features": ["product_category"],
      "p_value_threshold": 0.05
    },
    {
      "type": "custom",
      "output_name": "Distribution of Exploded Tags",
      "target_columns": ["tags"],
      "transformations": [
        {
          "action": "split_and_explode",
          "params": {"delimiter": ","}
        }
      ],
      "operation": "distribution"
    }
  ]
}

Responses

Success (200 OK):
Content-Type: text/csv
Body: A streaming response containing the generated report as CSV data. The Content-Disposition header will be set to trigger a file download with the output_filename.
Validation Error (422 Unprocessable Entity):
Content-Type: application/json
Body: A JSON object detailing the validation error, typically caused by a malformed request_data_str that does not conform to the schemas.
Server Error (500 Internal Server Error):
Content-Type: application/json
Body: A generic error message. The detailed traceback is logged to the server console and is not exposed to the client.

4. Local Setup and Execution

Dependencies

All required Python packages are defined in requirements.txt. Install them using:

pip install -r requirements.txt

Running the Server

The application is run via Uvicorn. From the backend/ directory, execute:

uvicorn app.main:app --reload

The server will be available at http://127.0.0.1:8000.

5. Testing

The backend has a suite of unit tests located in the tests/ directory. These tests verify the correctness of each individual analysis module.

To run the full test suite, navigate to the directory and execute:

pytest

A successful run will result in XX passed with no failures or warnings. This is the primary measure of application health and correctness.

6. Docker
Remnants of docker files and .yml are still left over from when deployment was an available option. Future stretch goals should include wrapping the project in an application so that
users can simply just download something akin to a .exe and have the package automatically download everything it needs to run. 