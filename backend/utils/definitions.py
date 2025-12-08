# backend/app/utils/definitions.py

# Master dictionary of statistical terms and their explanations
# Key: The term (e.g., 'Coefficient', 'P-value', 'IQR')
# Value: A dictionary containing 'title', 'description', and optional 'use_case', 'example', 'threshold_guidance', 'interpretation', 'expected_inputs', 'expected_output'.
STATISTICAL_DEFINITIONS = {
    # --- Analysis-Level Descriptions ---
    "Custom Analysis": {
        "title": "Custom Analysis",
        "description": "A flexible analysis type that allows you to apply various transformations and basic operations (like distribution, average, sum, median, mode) to specific columns. Ideal for tailored data exploration.",
        "use_case": "Use this analysis to get the distribution of 'Product Category', the average 'Discount Rate', or list unique 'Tags'.",
        "expected_inputs": "Requires one target column, which can be numerical or categorical depending on the chosen operation. Can also involve transformations.",
        "expected_output": "A table showing the result of the chosen operation (e.g., average, distribution counts, unique values) for the specified column(s).",
    },
    "Summary Statistics": {
        "title": "Summary Statistics",
        "description": "Provides a quick overview of the main features of a dataset, such as its central tendency (mean, median), variability (standard deviation), and shape (min, max, quartiles).",
        "use_case": "Use this analysis to get an overview of 'Sales Amount' distribution, average 'Units Sold', or range of 'Marketing Spend'.",
        "expected_inputs": "One or more numerical columns.",
        "expected_output": "A table listing key statistics (count, mean, std, min, max, quartiles) for each selected numerical column.",
    },
    "Correlation Analysis": {
        "title": "Correlation Analysis",
        "description": "Measures the statistical relationship between two or more variables. It helps identify if variables tend to change together (positive correlation), in opposite directions (negative correlation), or have no clear relationship.",
        "use_case": "Use this analysis to see if 'Marketing Spend' is related to 'Sales Amount', or if 'Units Sold' correlates with 'Discount Rate'.",
        "expected_inputs": "Two or more columns, which can be numerical (for Pearson correlation) or categorical (for Cramér's V).",
        "expected_output": "A table showing the correlation coefficient for each pair of selected columns, along with the type of correlation used.",
    },
    "Crosstab Analysis": {
        "title": "Crosstabulation (Crosstab) Analysis",
        "description": "Generates a table (contingency table) that displays the frequency distribution of two or more categorical variables. It helps in understanding the relationship between different categories by showing how many times each combination of categories appears in your data.",
        "use_case": "Use this analysis to see the breakdown of 'Product Category' by 'Region', or 'Return Flag' by 'Channel'.",
        "expected_inputs": "Two categorical columns (one for rows, one for columns in the table).",
        "expected_output": "A contingency table showing counts and optionally percentages for each combination of categories.",
    },
    "Outlier Detection": {
        "title": "Outlier Detection Analysis",
        "description": "Identifies data points that significantly deviate from the majority of observations. Outliers can indicate errors in data collection, unusual events, or important insights that warrant further investigation.",
        "use_case": "Use this analysis to find unusually high or low 'Sales Amount' or 'Shipment Delay Days'.",
        "expected_inputs": "One or more numerical columns.",
        "expected_output": "A list of identified outliers, including their original row index, column, value, and the method used.",
    },
    "Key Driver Analysis": {
        "title": "Key Driver Analysis (Regression)",
        "description": "Uses multiple linear regression to identify which independent variables (features) have the strongest statistical influence on a dependent variable (target). It quantifies the impact of each feature and assesses its significance.",
        "use_case": "Use this analysis to understand what factors (e.g., 'Marketing Spend', 'Units Sold') are 'driving' changes in 'Sales Amount'.",
        "expected_inputs": "One numerical target variable and one or more feature columns (numerical or categorical).",
        "expected_output": "A table showing coefficients, p-values, and R-squared for the regression model, indicating the strength and significance of each feature.",
    },
    "Time Series Analysis": {
        "title": "Time Series Analysis",
        "description": "Analyzes data points collected over a period of time to identify trends, seasonality, and other patterns. Used to understand how a metric behaves chronologically and can aid in forecasting.",
        "use_case": "Use this analysis to track 'Sales Amount' over 'Order Date' on a weekly or monthly basis.",
        "expected_inputs": "A date column, a numerical metric column, and a desired aggregation frequency.",
        "expected_output": "A time-ordered list of aggregated metric values (sum, average, or count) for each time period.",
    },
    # --- Common Statistical Terms (Reinstated Custom Operator Definitions) ---
    "Count": {
        "title": "Count",
        "description": "The number of non-missing values in a column or category.",
        "interpretation": "A count of 50 means there are 50 valid data points.",
        "expected_inputs": "Numerical or Categorical data.",
        "expected_output": "The total count.",
    },
    "Percentage": {
        "title": "Percentage",
        "description": "The proportion of a specific value or category relative to the total, expressed as a fraction of 100.",
        "interpretation": "A percentage of 25% means that value or category makes up one-quarter of the total.",
        "expected_inputs": "Numerical or Categorical data (typically used with distribution).",
        "expected_output": "The calculated percentage.",
    },
    "Average": {
        "title": "Average (Mean)",
        "description": "The sum of all values divided by the number of values. It's a common measure of central tendency.",
        "interpretation": "An average sales amount of $100 means the typical sale is $100.",
        "expected_inputs": "Numerical data.",
        "expected_output": "The calculated average.",
    },
    "Sum": {
        "title": "Sum",
        "description": "The total of all values in a numeric column.",
        "interpretation": "A sum of 1000 for sales amount means total sales for the period were $1000.",
        "expected_inputs": "Numerical data.",
        "expected_output": "The calculated sum.",
    },
    "Median": {
        "title": "Median",
        "description": "The middle value in a dataset when the values are arranged in order. If there's an even number of values, it's the average of the two middle values. It's less affected by extreme outliers than the average (mean).",
        "interpretation": "A median sales amount of $90 means half of sales are above $90 and half are below.",
        "expected_inputs": "Numerical data.",
        "expected_output": "The calculated median.",
    },
    "Mode": {
        "title": "Mode",
        "description": "The value(s) that appear most frequently in a dataset. A dataset can have one mode (unimodal), multiple modes (multimodal), or no mode if all values appear with the same frequency.",
        "interpretation": "A mode of 'Electronics' for product category means 'Electronics' is the most commonly occurring product category.",
        "expected_inputs": "Numerical or Categorical data.",
        "expected_output": "The most frequent value(s).",
    },
    "Standard Deviation": {
        "title": "Standard Deviation",
        "description": "A measure of the amount of variation or dispersion of a set of values. A low standard deviation indicates that the values tend to be close to the mean, while a high standard deviation indicates that the values are spread out over a wider range.",
        "interpretation": "It tells you how much individual data points typically deviate from the average.",
        "expected_inputs": "Numerical data.",
        "expected_output": "The calculated standard deviation.",
    },
    "Statistic": {
        "title": "Statistic (Summary Statistics)",
        "description": "A numerical value that summarizes some property of a sample of data. Common statistics include count, mean, standard deviation, minimum, maximum, and quartiles.",
        "expected_inputs": "Numerical data.",
        "expected_output": "A specific summary measure (e.g., mean, count, std).",
    },
    "Correlation Value": {
        "title": "Correlation Value (Pearson / Cramér's V)",
        "description": "A measure of the statistical relationship between two variables. It ranges from -1 to 1. \n- 1 indicates a perfect positive relationship.\n- -1 indicates a perfect negative relationship.\n- 0 indicates no linear relationship.",
        "interpretation": "Values closer to 1 or -1 indicate stronger relationships. Values near 0 indicate weak or no relationship.",
        "expected_inputs": "Two numerical or two categorical columns.",
        "expected_output": "A single numerical value between -1 and 1.",
    },
    "IQR (Interquartile Range)": {
        "title": "Interquartile Range (IQR) Method",
        "description": "A method for identifying outliers based on the spread of the middle 50% of the data. Values that fall below Q1 - (1.5 * IQR) or above Q3 + (1.5 * IQR) are typically considered outliers.",
        "threshold_guidance": "Common threshold is 1.5, making outliers rare. A lower threshold (e.g., 1.0) will identify more outliers, a higher threshold (e.g., 2.0) fewer.",
        "expected_inputs": "Numerical data.",
        "expected_output": "A list of identified outliers.",
    },
    "Z-score": {
        "title": "Z-score Method",
        "description": "A method for identifying outliers based on how many standard deviations a data point is from the mean. Values with an absolute Z-score greater than a specified 'Threshold' are considered outliers.",
        "threshold_guidance": "Common thresholds are 2.0 (mild outliers) or 3.0 (extreme outliers). A higher threshold means fewer outliers are detected.",
        "expected_inputs": "Numerical data.",
        "expected_output": "A list of identified outliers.",
    },
    "Coefficient": {
        "title": "Coefficient (Regression)",
        "description": "In regression, a coefficient indicates the strength and direction of the relationship between a feature and the target variable. Positive means target increases with feature; negative means target decreases. Magnitude shows strength.",
        "example": "A coefficient of 0.5 for 'Marketing Spend' on 'Sales Amount' means for every $1 increase in marketing spend, sales amount is estimated to increase by $0.50, holding other factors constant.",
        "expected_inputs": "Numerical feature and target variables.",
        "expected_output": "A numerical value representing the estimated change in the target for a one-unit change in the feature.",
    },
    "P-value": {
        "title": "P-value (Regression)",
        "description": "Helps determine statistical significance. A small P-value (typically < 0.05) suggests the observed relationship is unlikely by chance, implying the feature is a significant driver.",
        "threshold_guidance": "Commonly, P-values less than 0.05 (or 5%) are considered statistically significant.",
        "expected_inputs": "Numerical feature and target variables.",
        "expected_output": "A numerical value between 0 and 1.",
    },
    "R-squared": {
        "title": "R-squared (Regression)",
        "description": "Measures the proportion of the variance in the target variable that can be predicted from the feature variables. Ranges from 0 to 1. Higher R-squared indicates a better fit of the model to the data.",
        "interpretation": "An R-squared of 0.75 means 75% of the variation in the target variable is explained by the model's features.",
        "expected_inputs": "Numerical feature and target variables.",
        "expected_output": "A numerical value between 0 and 1.",
    },
    "Timestamp": {
        "title": "Timestamp (Time Series)",
        "description": "A specific point in time used to order and aggregate data chronologically.",
        "expected_inputs": "Date/Time data.",
        "expected_output": "A date/time value.",
    },
    "Aggregated Value": {
        "title": "Aggregated Value (Time Series)",
        "description": "The result of combining multiple data points within a defined time period (e.g., sum, average, count of a metric per day/week/month).",
        "expected_inputs": "Numerical data.",
        "expected_output": "The aggregated numerical result (sum, average, or count).",
    },
    # --- Other Specific Stats (from .describe() output) ---
    "count": {
        "title": "Count (Summary Stats)",
        "description": "The number of non-missing observations.",
        "expected_inputs": "Numerical data.",
        "expected_output": "An integer count.",
    },
    "mean": {
        "title": "Mean (Summary Stats)",
        "description": "The average value.",
        "expected_inputs": "Numerical data.",
        "expected_output": "A numerical average.",
    },
    "min": {
        "title": "Minimum (Summary Stats)",
        "description": "The smallest value.",
        "expected_inputs": "Numerical data.",
        "expected_output": "The minimum numerical value.",
    },
    "max": {
        "title": "Maximum (Summary Stats)",
        "description": "The largest value.",
        "expected_inputs": "Numerical data.",
        "expected_output": "The maximum numerical value.",
    },
    "std": {
        "title": "Standard Deviation (Summary Stats)",
        "description": "A measure of the spread of data points around the mean.",
        "expected_inputs": "Numerical data.",
        "expected_output": "A numerical standard deviation.",
    },
    "25%": {
        "title": "25th Percentile (Q1)",
        "description": "The value below which 25% of the data falls.",
        "expected_inputs": "Numerical data.",
        "expected_output": "A numerical value.",
    },
    "50%": {
        "title": "50th Percentile (Median)",
        "description": "The middle value of the dataset (median).",
        "expected_inputs": "Numerical data.",
        "expected_output": "A numerical value.",
    },
    "75%": {
        "title": "75th Percentile (Q3)",
        "description": "The value below which 75% of the data falls.",
        "expected_inputs": "Numerical data.",
        "expected_output": "A numerical value.",
    },
}


# CRITICAL FIX: New function to generate a plain text string of all definitions
def get_all_definitions_as_text() -> str:
    """
    Formats all statistical definitions into a single, human-readable plain text string.
    Definitions are grouped by analysis type and sorted within groups.
    """
    output_lines = ["--- Report Auto: Statistical Terminology Definitions ---", ""]
    output_lines.append(
        "This document provides explanations for the various analysis types, statistical terms, and metrics that may appear in your generated reports."
    )
    output_lines.append(
        "It is intended as a quick reference guide to help interpret your data."
    )
    output_lines.append("\n=======================================================\n")

    # Define a consistent order for analysis types for grouping
    analysis_type_order = [
        "Custom Analysis",
        "Summary Statistics",
        "Correlation Analysis",
        "Crosstab Analysis",
        "Outlier Detection",
        "Key Driver Analysis",
        "Time Series Analysis",
    ]

    # Map analysis types to their associated terms for grouping
    # This structure helps control the order and grouping of terms in the output
    grouped_terms_map = {
        "Custom Analysis": ["Average", "Sum", "Median", "Mode", "Count", "Percentage"],
        "Summary Statistics": [
            "Statistic",
            "count",
            "mean",
            "std",
            "min",
            "max",
            "25%",
            "50%",
            "75%",
            "Standard Deviation",
        ],
        "Correlation Analysis": ["Correlation Value"],
        "Crosstab Analysis": ["Count", "Percentage"],
        "Outlier Detection": ["IQR (Interquartile Range)", "Z-score"],
        "Key Driver Analysis": ["Coefficient", "P-value", "R-squared"],
        "Time Series Analysis": ["Timestamp", "Aggregated Value"],
    }

    for analysis_title in analysis_type_order:
        definition_data = STATISTICAL_DEFINITIONS.get(analysis_title)
        if definition_data:
            output_lines.append(f"\n### {definition_data['title']} ###")
            output_lines.append(f"Description: {definition_data['description']}")
            if "use_case" in definition_data:
                output_lines.append(f"Use Case: {definition_data['use_case']}")
            # CRITICAL FIX: Added Expected Inputs for analysis-level
            if "expected_inputs" in definition_data:
                output_lines.append(
                    f"Expected Inputs: {definition_data['expected_inputs']}"
                )
            # CRITICAL FIX: Added Expected Output for analysis-level
            if "expected_output" in definition_data:
                output_lines.append(
                    f"Expected Output: {definition_data['expected_output']}"
                )
            output_lines.append("-" * 30)  # Separator

        # Add specific terms related to this analysis type
        terms_for_group = grouped_terms_map.get(analysis_title, [])
        for term_key in sorted(terms_for_group):  # Sort terms within each group
            term_def = STATISTICAL_DEFINITIONS.get(term_key)
            # Ensure the term is not the analysis_title itself (already printed)
            if term_def and term_key != analysis_title:
                output_lines.append(f"  - {term_def['title']}:")
                output_lines.append(f"    Description: {term_def['description']}")
                if "example" in term_def:
                    output_lines.append(f"    Example: {term_def['example']}")
                if "threshold_guidance" in term_def:
                    output_lines.append(
                        f"    Threshold Guidance: {term_def['threshold_guidance']}"
                    )
                if "interpretation" in term_def:
                    output_lines.append(
                        f"    Interpretation: {term_def['interpretation']}"
                    )
                # CRITICAL FIX: Added Expected Inputs for terms
                if "expected_inputs" in term_def:
                    output_lines.append(
                        f"    Expected Inputs: {term_def['expected_inputs']}"
                    )
                # CRITICAL FIX: Added Expected Output for terms
                if "expected_output" in term_def:
                    output_lines.append(
                        f"    Expected Output: {term_def['expected_output']}"
                    )
                output_lines.append("")  # Blank line for spacing

    return "\n".join(output_lines)
