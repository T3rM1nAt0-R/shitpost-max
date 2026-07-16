import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from trie_stats_plugin import TrieStatsPlugin

KNOWN_NODE_COUNTS = [3, 4, 5, 8, 8]
KNOWN_DEPTHS = [3, 3, 4, 4, 4]


def test_insertion_stats_match_known_values(tmp_path, monkeypatch):
    plugin = TrieStatsPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    node_counts = []
    depths = []
    for _ in range(5):
        result = plugin.produce()
        node_counts.append(result["node_count"])
        depths.append(result["max_depth"])

    assert node_counts == KNOWN_NODE_COUNTS
    assert depths == KNOWN_DEPTHS


def test_words_cycle_in_order(tmp_path, monkeypatch):
    plugin = TrieStatsPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    words = []
    for _ in range(7):
        result = plugin.produce()
        words.append(result["word"])

    assert words == ["cat", "car", "card", "dog", "do", "cat", "car"]
