import re
from report_auto.utils import compute_percentages, clean_list_string, split_pattern_for

def test_compute_percentages_deterministic():
    out = compute_percentages({"a":1, "b":1, "c":1})
    assert sum(out.values()) == 100
    assert out["a"] == 34  # deterministic tie-break

def test_clean_list_string():
    assert clean_list_string("Hello_world, 50% done (beta) / foo") == "Hello world, 50 done beta foo"

def test_split_pattern_for():
    s = "a | b|c "
    assert re.split(split_pattern_for("|"), s) == ["a", "b", "c"]
    s2 = "a   b   c"
    assert re.split(split_pattern_for(None), s2) == ["a","b","c"]