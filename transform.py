import pandas as pd
import re
from utils import clean_list_string

# Data Manipulation

"""
COLUMN
Is the column in the report to be manipulated.
-------------------------------------
VALUE
Is an optional input that will target a single value present within the reporting file.
-------------------------------------
AGGREGATE
To always be set as “yes” unless when blank/NaN value is desired. # Is there a better use case?
-------------------------------------
ROOT ONLY
When the desired output is at index[0]. # this is for when the desired output is the 1st word or index of a string
-------------------------------------
DELIMITER
Any character to separate by.
-------------------------------------
SEPARATE NODES
To be used for when there are nested values and alongside DELIMITER.
-------------------------------------
DUPLICATE
To identify duplicates.
-------------------------------------
AVERAGE
To output the average within a column this is float int any other digit base.
-------------------------------------
CLEAN
To clean any marking from a string, this is to only output character
"""


def generate_column_report(report_df: pd.DataFrame, config_df: pd.DataFrame) -> list:
    # total tasks used / not calling atm
    total_config = len(config_df)
    # tatal rows read / replacing total config atm
    total_rows = len(report_df)
    cfg = config_df.copy()
    cfg.columns = cfg.columns.str.strip().str.lower().str.replace(" ", "_")
    cfg["column"] = (
        cfg["column"].astype(str).str.strip().str.lower().str.replace(" ", "_")
    )

    flags = [
        "aggregate",
        "root_only",
        "separate_nodes",
        "average",
        "duplicate",
        "clean",
    ]
    for flag in flags:
        if flag in cfg.columns:
            cfg[flag] = (
                cfg[flag]
                .fillna("False")
                .astype(str)
                .str.strip()
                .str.lower()
                .isin(["yes", "true"])
            )
        else:
            cfg[flag] = False

    if "value" in cfg.columns:
        cfg["value"] = cfg["value"].fillna("").astype(str).str.lower()
    else:
        cfg["value"] = ""

    if "delimiter" in cfg.columns:
        # Do not set any default; missing/NaN means "no delimiter provided"
        pass
    else:
        cfg["delimiter"] = ""

    sections = []
    sections.append([["Total rows", "", total_rows]])

    for col_name in cfg["column"].unique():
        if col_name not in report_df.columns:
            continue

        hdr = col_name.replace("_", " ").upper()

        is_clean = cfg.loc[cfg["column"] == col_name, "clean"].any()
        if is_clean:
            clean_section = [[hdr, "", "Cleaned"]]
            cleaned = report_df[col_name].apply(clean_list_string)
            for val in cleaned:
                clean_section.append(["", "", val])
            sections.append(clean_section)
            continue

        if cfg.loc[cfg["column"] == col_name, "duplicate"].any():
            s = report_df[col_name].fillna("").astype(str).str.strip().str.lower()
            # raw = report_df[col_name].fillna("").astype(str)
            counts = s.value_counts()
            duplicate = counts[counts > 1]
            section = [[hdr, "Duplicates", "Instances"]]
            for value, cnt in duplicate.items():
                section.append(["", value, cnt])
            sections.append(section)
            continue

        if cfg.loc[cfg["column"] == col_name, "average"].any():
            raw = report_df[col_name].astype(str).str.strip()
            nums = pd.to_numeric(raw.str.rstrip("%"), errors="coerce")
            if nums.notna().sum() == 0:
                sections.append([[hdr, "", "Average"], ["No numeric data", "", ""]])
            else:
                unit = "%" if raw.str.endswith("%").any() else ""
                avg = nums.mean()
                sections.append([[hdr, "", "Average"], ["", "", f"{avg:.2f}{unit}"]])
            continue

        entries = cfg[cfg["column"] == col_name]
        label_counts = {}
        search_value = entries[entries["value"] != ""]

        if not search_value.empty:
            for _, r in search_value.iterrows():
                series = report_df[col_name].fillna("").astype(str)
                # Delimiter logic for separate_nodes
                if r["separate_nodes"]:
                    delim = r["delimiter"] if pd.notna(r["delimiter"]) and str(r["delimiter"]).strip() != "" else None
                    if delim:
                        items = (
                            series.str.split(rf"\s*{re.escape(str(delim))}\s*", regex=True)
                                  .explode()
                                  .dropna()
                                  .str.strip()
                                  .str.lower()
                            # .apply(clean_list_string) | Not applying cleaning here, as below
                        )
                    else:
                        # No delimiter provided; treat the entire cell as a single token
                        items = series.fillna("").astype(str).str.strip().str.lower()
                    cnt = int((items == str(r["value"]).strip().lower()).sum())
                else:
                    delim = r["delimiter"] if pd.notna(r["delimiter"]) and str(r["delimiter"]).strip() != "" else None
                    if r["root_only"] and delim:
                        series = series.str.split(re.escape(str(delim)), expand=True)[0]
                    if delim:
                        d = re.escape(str(delim))
                        v = re.escape(str(r["value"]).strip().lower())
                        pattern = rf"(?:^|{d})\s*{v}\s*(?:{d}|$)"
                        cnt = int(series.str.lower().str.contains(pattern, regex=True).sum())
                    else:
                        # Without a delimiter, perform normalized equality on the whole field
                        cnt = int(series.str.strip().str.lower().eq(str(r["value"]).strip().lower()).sum())
                label = r["value"] or "None"
                label_counts[label] = cnt
        else:
            for _, r in entries.iterrows():
                series = report_df[col_name].fillna("").astype(str)
                if r["separate_nodes"]:
                    delim = r["delimiter"] if pd.notna(r["delimiter"]) and str(r["delimiter"]).strip() != "" else None
                    if delim:
                        items = (
                            series.str.split(rf"\s*{re.escape(str(delim))}\s*", regex=True)
                                  .explode()
                                  .dropna()
                                  .str.strip()
                                  .str.lower()
                        )
                    else:
                        items = series.fillna("").astype(str).str.strip().str.lower()
                    for val in items:
                        label = val or "None"
                        label_counts[label] = label_counts.get(label, 0) + 1
                elif r["aggregate"]:
                    delim = r["delimiter"] if pd.notna(r["delimiter"]) and str(r["delimiter"]).strip() != "" else None
                    if r["root_only"] and delim:
                        series = series.str.split(re.escape(str(delim)), expand=True)[0]
                    s = series.str.strip().str.lower()
                    for val in sorted(s.unique()):
                        if not val.strip():
                            continue
                        cnt = int((s == val).sum())
                        label_counts[val] = cnt
                else:
                    delim = r["delimiter"] if pd.notna(r["delimiter"]) and str(r["delimiter"]).strip() != "" else None
                    if r["root_only"] and delim:
                        series = series.str.split(re.escape(str(delim)), expand=True)[0]
                    if delim:
                        d = re.escape(str(delim))
                        v = re.escape(str(r["value"]).strip().lower())
                        pattern = rf"(?:^|{d})\s*{v}\s*(?:{d}|$)"
                        cnt = int(series.str.lower().str.contains(pattern, regex=True).sum())
                    else:
                        cnt = int(series.str.strip().str.lower().eq(str(r["value"]).strip().lower()).sum())
                    label = r["value"] or "None"
                    label_counts[label] = label_counts.get(label, 0) + cnt

        section = [[hdr, "%", "Count"]]
        for label, cnt in label_counts.items():
            pct = round(cnt / total_rows * 100, 2) if total_rows else 0
            section.append([label, f"{pct:.2f}%", cnt])
        sections.append(section)

    return sections
