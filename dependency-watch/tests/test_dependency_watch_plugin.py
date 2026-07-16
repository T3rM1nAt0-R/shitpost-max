import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from dependency_watch_plugin import DependencyWatchPlugin

EXPECTED = [
    ("2026-01-01", 12, 0),
    ("2026-02-01", 15, 3),
    ("2026-03-01", 15, 0),
    ("2026-04-01", 19, 4),
    ("2026-05-01", 22, 3),
]


def test_full_cycle_matches_ground_truth(tmp_path, monkeypatch):
    plugin = DependencyWatchPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for expected_date, expected_count, expected_delta in EXPECTED:
        result = plugin.produce()
        assert result["snapshot_date"] == expected_date
        assert result["dependency_count"] == expected_count
        assert result["delta"] == expected_delta


def test_wraps_around(tmp_path, monkeypatch):
    plugin = DependencyWatchPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for _ in range(len(EXPECTED)):
        plugin.produce()
    result = plugin.produce()
    assert result["snapshot_date"] == "2026-01-01"
    assert result["delta"] == 0
