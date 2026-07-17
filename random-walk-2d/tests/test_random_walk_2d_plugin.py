import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from random_walk_2d_plugin import RandomWalk2DPlugin

KNOWN_POSITIONS = [
    (0, -1), (0, -2), (0, -3), (0, -4), (0, -3), (0, -4), (0, -5), (0, -4),
    (0, -5), (0, -6), (0, -5), (1, -5), (2, -5), (2, -4), (2, -5),
]


def test_walk_matches_known_deterministic_sequence(tmp_path, monkeypatch):
    plugin = RandomWalk2DPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    positions = []
    for _ in range(len(KNOWN_POSITIONS)):
        result = plugin.produce()
        positions.append((result["x"], result["y"]))

    assert positions == KNOWN_POSITIONS


def test_distance_squared_matches_position(tmp_path, monkeypatch):
    plugin = RandomWalk2DPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    for _ in range(20):
        result = plugin.produce()
        assert result["distance_squared"] == result["x"] ** 2 + result["y"] ** 2
