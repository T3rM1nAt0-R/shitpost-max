import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from sierpinski_chaos_plugin import SierpinskiChaosPlugin

KNOWN_POINTS = [
    (0.75, 0.25), (0.625, 0.558), (0.5625, 0.712), (0.2812, 0.356),
    (0.3906, 0.611), (0.6953, 0.3055), (0.3477, 0.1527), (0.6738, 0.0764),
]


def test_8_points_match_known_sequence(tmp_path, monkeypatch):
    plugin = SierpinskiChaosPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen = []
    for _ in range(8):
        result = plugin.produce()
        seen.append((result["x"], result["y"]))

    assert seen == KNOWN_POINTS
