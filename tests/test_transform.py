import pandas as pd
from report_auto.transform import generate_column_report
from report_auto.generator import assemble_report

def test_pipeline_smoke():
    df = pd.DataFrame({
        "category": ["apple|banana", "banana", "apple|cherry", "", "banana|banana"],
        "score": [10, 20, None, 40, 20],
        "notes": ["Hello_world", "50% done (beta)", "foo/bar", "", None],
        "dup_col": ["x", "y", "x", "z", "y"],
    })
    cfg = pd.DataFrame([
        {"column": "category", "aggregate": "yes", "separate_nodes": "yes", "delimiter": "|"},
        {"column": "dup_col", "duplicate": "yes"},
        {"column": "score", "average": "yes"},
        {"column": "notes", "clean": "yes"},
    ])
    blocks = generate_column_report(df, cfg)
    out = assemble_report(blocks)
    assert not out.empty