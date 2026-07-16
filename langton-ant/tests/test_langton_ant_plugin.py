import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from langton_ant_plugin import LangtonAntPlugin

KNOWN = [(11, 10, 1), (11, 11, 2), (10, 11, 3), (10, 10, 4), (9, 10, 3)]


def test_first_5_steps_match_known_sequence(tmp_path, monkeypatch):
    plugin = LangtonAntPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen = []
    for _ in range(5):
        result = plugin.produce()
        seen.append((result["x"], result["y"], result["black_cells"]))

    assert seen == KNOWN
