import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from iterated_prisoner_plugin import IteratedPrisonerPlugin

KNOWN = [
    ("C", "D", 0, 5), ("D", "D", 1, 6), ("D", "D", 2, 7),
    ("D", "D", 3, 8), ("D", "D", 4, 9), ("D", "D", 5, 10),
]


def test_6_rounds_match_known_sequence(tmp_path, monkeypatch):
    plugin = IteratedPrisonerPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen = []
    for _ in range(6):
        result = plugin.produce()
        seen.append((result["a_move"], result["b_move"], result["a_score"], result["b_score"]))

    assert seen == KNOWN
