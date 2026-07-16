import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from git_blame_stats_plugin import GitBlameStatsPlugin

EXPECTED = [
    ("alice", 4210),
    ("bob", 3150),
    ("carol", 1800),
    ("dave", 620),
]


def test_full_cycle_matches_ground_truth(tmp_path, monkeypatch):
    plugin = GitBlameStatsPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for expected_author, expected_lines in EXPECTED:
        result = plugin.produce()
        assert result["author"] == expected_author
        assert result["line_count"] == expected_lines


def test_wraps_around(tmp_path, monkeypatch):
    plugin = GitBlameStatsPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for _ in range(len(EXPECTED)):
        plugin.produce()
    result = plugin.produce()
    assert result["author"] == "alice"
