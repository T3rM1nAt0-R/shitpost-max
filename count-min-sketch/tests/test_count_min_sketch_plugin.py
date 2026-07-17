import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from count_min_sketch_plugin import CountMinSketchPlugin


def test_estimate_never_underestimates_the_true_count(tmp_path, monkeypatch):
    plugin = CountMinSketchPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    for _ in range(40):
        result = plugin.produce()
        assert result["estimate"] >= result["exact"]


def test_exact_counts_match_true_frequency_after_one_full_cycle(tmp_path, monkeypatch):
    plugin = CountMinSketchPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    results = [plugin.produce() for _ in range(len(plugin._STREAM))]
    exact_by_item = {r["item"]: r["exact"] for r in results}

    assert exact_by_item["apple"] == 4
    assert exact_by_item["banana"] == 2
    assert exact_by_item["cherry"] == 1
    assert exact_by_item["date"] == 1


def test_hash_is_deterministic_across_instances():
    p1 = CountMinSketchPlugin()
    p2 = CountMinSketchPlugin()
    for row in range(CountMinSketchPlugin._DEPTH):
        assert p1._hash("apple", row) == p2._hash("apple", row)
