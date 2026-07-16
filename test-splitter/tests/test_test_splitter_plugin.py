import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from test_splitter_plugin import TestSplitterPlugin

EXPECTED = [
    (0, ["test_api.py", "test_cache.py"], 27.0),
    (1, ["test_views.py", "test_models.py", "test_utils.py"], 26.0),
    (2, ["test_auth.py", "test_tasks.py", "test_forms.py"], 27.0),
]


def test_full_cycle_matches_ground_truth(tmp_path, monkeypatch):
    plugin = TestSplitterPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for expected_index, expected_files, expected_total in EXPECTED:
        result = plugin.produce()
        assert result["group_index"] == expected_index
        assert result["files"] == expected_files
        assert result["total_seconds"] == expected_total


def test_wraps_around(tmp_path, monkeypatch):
    plugin = TestSplitterPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for _ in range(len(EXPECTED)):
        plugin.produce()
    result = plugin.produce()
    assert result["group_index"] == 0
