import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from schelling_segregation_plugin import SchellingSegregationPlugin

KNOWN_MOVES = [16, 8, 1]


def test_first_3_ticks_match_known_moves(tmp_path, monkeypatch):
    plugin = SchellingSegregationPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen = []
    for _ in range(3):
        result = plugin.produce()
        seen.append(result["moves"])

    assert seen == KNOWN_MOVES
