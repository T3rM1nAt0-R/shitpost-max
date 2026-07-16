import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from birthday_paradox_plugin import BirthdayParadoxPlugin

KNOWN = [23, 55, 32, 27, 23]


def test_first_5_trials_match_known_values(tmp_path, monkeypatch):
    plugin = BirthdayParadoxPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen = []
    for _ in range(5):
        result = plugin.produce()
        seen.append(result["people"])

    assert seen == KNOWN
