import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from branch_age_tracker_plugin import BranchAgeTrackerPlugin

EXPECTED = [
    ("archive/old-api", 400),
    ("experiment/rewrite", 145),
    ("fix/login-bug", 12),
    ("feature/dark-mode", 3),
    ("main", 0),
]


def test_full_cycle_matches_ground_truth(tmp_path, monkeypatch):
    plugin = BranchAgeTrackerPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for expected_branch, expected_days in EXPECTED:
        result = plugin.produce()
        assert result["branch"] == expected_branch
        assert result["days_stale"] == expected_days


def test_wraps_around(tmp_path, monkeypatch):
    plugin = BranchAgeTrackerPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for _ in range(len(EXPECTED)):
        plugin.produce()
    result = plugin.produce()
    assert result["branch"] == "archive/old-api"
