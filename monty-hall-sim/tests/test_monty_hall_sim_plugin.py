import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from monty_hall_sim_plugin import MontyHallSimPlugin


def test_20_trials_match_known_counts(tmp_path, monkeypatch):
    plugin = MontyHallSimPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    result = None
    for _ in range(20):
        result = plugin.produce()

    assert result["stay_wins"] == 4
    assert result["switch_wins"] == 16
    assert result["trials"] == 20


def test_switch_beats_stay_over_many_trials(tmp_path, monkeypatch):
    plugin = MontyHallSimPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    result = None
    for _ in range(50):
        result = plugin.produce()

    assert result["switch_wins"] > result["stay_wins"]
