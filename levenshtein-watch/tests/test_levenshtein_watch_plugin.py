import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from levenshtein_watch_plugin import LevenshteinWatchPlugin

KNOWN_DISTANCES = [3, 2, 5, 0, 3]


def test_levenshtein_matches_known_values():
    plugin = LevenshteinWatchPlugin()
    computed = [plugin._levenshtein(a, b) for a, b in plugin._PAIRS]
    assert computed == KNOWN_DISTANCES


def test_produce_cycles_through_pairs_in_order(tmp_path, monkeypatch):
    plugin = LevenshteinWatchPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen_distances = []
    for _ in range(5):
        result = plugin.produce()
        seen_distances.append(result["distance"])

    assert seen_distances == KNOWN_DISTANCES


def test_cycles_back_to_first_pair(tmp_path, monkeypatch):
    plugin = LevenshteinWatchPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    for _ in range(5):
        plugin.produce()

    result = plugin.produce()
    assert result["a"] == "kitten"
    assert result["b"] == "sitting"
    assert result["distance"] == 3
