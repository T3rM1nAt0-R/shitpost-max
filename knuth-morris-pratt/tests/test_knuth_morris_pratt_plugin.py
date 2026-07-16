import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from knuth_morris_pratt_plugin import KnuthMorrisPrattPlugin

KNOWN = [
    ("ABABCABAB", [0, 0, 1, 2, 0, 1, 2, 3, 4], [10, 25]),
    ("AABAACAABAA", [0, 1, 0, 1, 2, 0, 1, 2, 3, 4, 5], [0, 11]),
    ("ABAB", [0, 0, 1, 2], [0, 2, 4]),
]


def test_failure_and_search_match_known_values():
    plugin = KnuthMorrisPrattPlugin()
    for pattern, text in plugin._PAIRS:
        expected = next(k for k in KNOWN if k[0] == pattern)
        assert plugin._kmp_failure(pattern) == expected[1]
        assert plugin._kmp_search(text, pattern) == expected[2]


def test_produce_cycles_through_pairs_in_order(tmp_path, monkeypatch):
    plugin = KnuthMorrisPrattPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    for pattern, _, matches in KNOWN:
        result = plugin.produce()
        assert result["pattern"] == pattern
        assert result["matches"] == matches
        assert result["match_count"] == len(matches)


def test_cycles_back_to_first_pair(tmp_path, monkeypatch):
    plugin = KnuthMorrisPrattPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    for _ in range(3):
        plugin.produce()

    result = plugin.produce()
    assert result["pattern"] == "ABABCABAB"
