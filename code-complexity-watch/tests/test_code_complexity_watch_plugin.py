import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from code_complexity_watch_plugin import CodeComplexityWatchPlugin

EXPECTED = [
    ("handle_request", 14),
    ("validate_input", 9),
    ("parse_config", 6),
    ("main", 3),
    ("helper", 1),
]


def test_full_cycle_matches_ground_truth(tmp_path, monkeypatch):
    plugin = CodeComplexityWatchPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for expected_func, expected_score in EXPECTED:
        result = plugin.produce()
        assert result["function"] == expected_func
        assert result["complexity"] == expected_score


def test_wraps_around(tmp_path, monkeypatch):
    plugin = CodeComplexityWatchPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for _ in range(len(EXPECTED)):
        plugin.produce()
    result = plugin.produce()
    assert result["function"] == "handle_request"
