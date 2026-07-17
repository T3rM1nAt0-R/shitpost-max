import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from stern_brocot_plugin import SternBrocotPlugin

KNOWN_SEQUENCE = [
    (1, 1), (1, 2), (2, 1), (1, 3), (2, 3), (3, 2), (3, 1),
    (1, 4), (2, 5), (3, 5), (3, 4), (4, 3), (5, 3), (5, 2), (4, 1),
]


def test_bfs_sequence_matches_known_values(tmp_path, monkeypatch):
    plugin = SternBrocotPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen = []
    for _ in range(len(KNOWN_SEQUENCE)):
        result = plugin.produce()
        seen.append((result["numerator"], result["denominator"]))

    assert seen == KNOWN_SEQUENCE


def test_fractions_are_always_positive(tmp_path, monkeypatch):
    plugin = SternBrocotPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    for _ in range(50):
        result = plugin.produce()
        assert result["numerator"] > 0
        assert result["denominator"] > 0
