
Auto Report Generator for Data Loading, Standardizing, Transforming, and Conflating

In an effort to stream-line the reporting process, this Generator assists with manipulating Data points and generating a clean and easily readable data set that anyone can read and use. Process consist of:

~ Data Reading: extract.py
~ Data Standardizing: utils.py 
~ Data Manipulation: transform.py
~ Data Assembly: report_generator.py
~ Data Reporting: auto_report.py

To run script in terminal:
python auto_report.py \
  --config-path path/to/report_config.csv


### Current Implementation allows for the following tasks:
  VALUE - Specify key to search for.
  AGGREGATE - Allow manipulations.
  ROOT ONLY - Retrieve the first index seperated by DELIMITTER.
  DELIMITTER - A special character to be used for seperations.
  SEPERATE NODES - Coupled with DELIMITTER, used to seperate tokens/nodes in string.
  DUPLICATE - Catches all duplicates in Column, also useful for instances visual.
  AVERAGE - Generates an average between all integer based columns.
  CLEAN - Clean columns from all special characters except commas, this includes double spaces.
  INTENDED PURPOSE - Comment Section to illustrate the intended purpose of your task.

### Correlations Insights:
  INSIGHTS ENABLED - Yes / No - Set to allow correlations insights
  INSIGHTS THRESHOLD - Set to determine % correlation met to output
  INSIGHTS SOURCES - Source to compare to
  INSIGHTS TARGETS - Sources to compare against

## Configuration Contract

Each row in the configuration table defines a reporting instruction for a single column.

### Required
| Column | Meaning |
|--------|---------|
| `COLUMN` | The name of the data column to inspect. Data columns are normalized to lowercase and underscores. |

### Optional Parameters
| Field | Purpose | Behavior |
|-------|---------|----------|
| `VALUE` | Target a specific value only (case-insensitive) | If blank, all values are considered |
| `DELIMITER` | Token separator | No default. When blank, full-cell comparisons are used. |
| `AGGREGATE` | Count all unique values or tokens discovered | Accepts yes/true/y/1 |
| `SEPARATE NODES` | Split a cell into multiple tokens using delimiter | Accepts yes/true/y/1. Requires `DELIMITER`. |
| `ROOT ONLY` | Select only first token before delimiter | Used with or without AGGREGATE |
| `DUPLICATE` | Report any values that occur more than once | Case-insensitive after trimming |
| `AVERAGE` | Compute column mean | Ignores non-numeric values. Preserves % unit if present. |
| `CLEAN` | Produce a cleaned view of column contents | Removes special symbols except letters, digits, spaces, commas |

### Truthy values
Flags accept case-insensitive:
```
yes, true
```

## Output Format

The resulting CSV contains multiple stacked sections, each separated by a blank row (`["", "", ""]`).

Common section shapes:

| Task | Header Row | Rows Produced |
|------|-------------|----------------|
| Total Row Count | `Total rows` | exactly 1 |
| Duplicate Detection | `[COLUMN, "Duplicates", "Instances"]` | One per duplicate value |
| Average | `[COLUMN, "", "Average"]` | One line with aggregated metric |
| Frequency / Aggregation | `[COLUMN, "%", "Count"]` | One per value discovered |
| Cleaned Output | `[COLUMN, "", "Cleaned"]` | One per input row |

Percentages are calculated as:
```
count / total_rows * 100, rounded to 2 decimals
```
Zero rows yields 0%.

---

## Multi-Sheet Mode

If `--multi-sheet` is provided with an Excel file:
- Each sheet is processed independently
- Each output file is suffixed with the sheet name (e.g., `_Sheet1.csv`)

---

## Recommended Best Practices

- Normalize config column names to match extracted data (`store_name`, not `Store Name`)
- Set `VALUE` when verifying a hypothesis about a fixed expected label
- Use `SEPARATE NODES + DELIMITER` for list-style fields
- Keep unused config columns for documentation, such as `INTENDED PURPOSE`

---