import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from multi_armed_bandit_plugin import MultiArmedBanditPlugin

KNOWN_ARMS = [0, 1, 2, 1, 1, 1, 1]


def test_7_pulls_match_known_arm_sequence(tmp_path, monkeypatch):
    plugin = MultiArmedBanditPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen = []
    for _ in range(7):
        result = plugin.produce()
        seen.append(result["arm"])

    assert seen == KNOWN_ARMS
