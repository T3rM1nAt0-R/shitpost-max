import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from simhash_near_dup_plugin import SimhashNearDupPlugin

KNOWN_DISTANCES = [9, 14, 0]


def test_distances_match_known_values(tmp_path, monkeypatch):
    plugin = SimhashNearDupPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen = []
    for _ in range(3):
        result = plugin.produce()
        seen.append(result["hamming_distance"])

    assert seen == KNOWN_DISTANCES


def test_identical_text_always_has_zero_distance():
    plugin = SimhashNearDupPlugin()
    fp = plugin._simhash("some completely different sentence")
    assert plugin._hamming(fp, fp) == 0
