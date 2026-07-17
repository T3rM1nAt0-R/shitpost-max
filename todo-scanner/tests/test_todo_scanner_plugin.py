import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from todo_scanner_plugin import TodoScannerPlugin

EXPECTED = [
    ("auth.py", {"TODO": 2, "FIXME": 1, "HACK": 0, "XXX": 0}, 3),
    ("utils.py", {"TODO": 0, "FIXME": 0, "HACK": 1, "XXX": 1}, 2),
    ("models.py", {"TODO": 0, "FIXME": 0, "HACK": 0, "XXX": 0}, 0),
]


def test_full_cycle_matches_ground_truth(tmp_path, monkeypatch):
    plugin = TodoScannerPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for expected_name, expected_counts, expected_total in EXPECTED:
        result = plugin.produce()
        assert result["filename"] == expected_name
        assert result["counts"] == expected_counts
        assert result["total"] == expected_total


def test_wraps_around(tmp_path, monkeypatch):
    plugin = TodoScannerPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for _ in range(len(EXPECTED)):
        plugin.produce()
    result = plugin.produce()
    assert result["filename"] == "auth.py"
    assert result["total"] == 3
