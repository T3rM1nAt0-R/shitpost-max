import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from forest_fire_sim_plugin import ForestFireSimPlugin

KNOWN = [(32, 3, 1), (27, 5, 4), (20, 7, 9), (11, 9, 16), (0, 11, 25), (0, 0, 36)]


def test_6_generations_match_known_sequence(tmp_path, monkeypatch):
    plugin = ForestFireSimPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen = []
    for _ in range(6):
        result = plugin.produce()
        seen.append((result["trees"], result["burning"], result["empty"]))

    assert seen == KNOWN


def test_resets_after_fire_dies_out(tmp_path, monkeypatch):
    plugin = ForestFireSimPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    for _ in range(6):
        plugin.produce()

    result = plugin.produce()
    assert (result["trees"], result["burning"], result["empty"]) == (32, 3, 1)
