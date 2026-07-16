import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from radix_sort_tick_plugin import RadixSortTickPlugin

KNOWN_PASSES = [
    [170, 90, 802, 2, 24, 45, 75, 66],
    [802, 2, 24, 45, 66, 170, 75, 90],
    [2, 24, 45, 66, 75, 90, 170, 802],
]


def test_passes_match_known_sequence(tmp_path, monkeypatch):
    plugin = RadixSortTickPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen = []
    for _ in range(3):
        result = plugin.produce()
        seen.append(result["array"])

    assert seen == KNOWN_PASSES
    assert seen[-1] == sorted(RadixSortTickPlugin._ARRAY)


def test_resets_after_fully_sorted(tmp_path, monkeypatch):
    plugin = RadixSortTickPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    for _ in range(3):
        plugin.produce()

    result = plugin.produce()
    assert result["array"] == RadixSortTickPlugin._radix_pass(RadixSortTickPlugin._ARRAY, 1)
