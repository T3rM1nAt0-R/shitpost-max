import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from timsort_metrics_plugin import TimsortMetricsPlugin

KNOWN = [(10, 5), (4, 3), (0, 0), (16, 8)]


def test_counting_merge_sort_matches_known_values():
    plugin = TimsortMetricsPlugin()
    for arr, (comparisons, merges) in zip(plugin._ARRAYS, KNOWN):
        _, c, m = plugin._counting_merge_sort(arr)
        assert (c, m) == (comparisons, merges)


def test_produce_cycles_through_arrays_in_order(tmp_path, monkeypatch):
    plugin = TimsortMetricsPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen = []
    for _ in range(4):
        result = plugin.produce()
        seen.append((result["comparisons"], result["merges"]))

    assert seen == KNOWN
