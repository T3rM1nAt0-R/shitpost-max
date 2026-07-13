import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)
from sorting_race_plugin import bubble_sort, insertion_sort, selection_sort, merge_sort, SortingRacePlugin

ALGOS = [bubble_sort, insertion_sort, selection_sort, merge_sort]

def test_all_sort_correctly():
    data = [5, 3, 8, 1, 9, 2, 7, 4, 6, 0]
    for fn in ALGOS:
        assert fn(list(data)) == sorted(data), f"{fn.__name__} produced wrong output"

def test_all_do_not_mutate_input():
    data = [5, 3, 8, 1, 9, 2, 7, 4, 6, 0]
    original = list(data)
    for fn in ALGOS:
        copy = list(data)
        fn(copy)
        assert copy == original, f"{fn.__name__} mutated its input in place"

def test_produce_runs(tmp_path, monkeypatch):
    p = SortingRacePlugin()
    monkeypatch.setattr(p, "_plugin_dir", lambda: str(tmp_path))
    r1 = p.produce()
    r2 = p.produce()
    assert r1["algorithm"] != r2["algorithm"]  # round-robin advances
