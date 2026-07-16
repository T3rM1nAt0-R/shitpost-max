import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from makefile_help_plugin import MakefileHelpPlugin

EXPECTED = [
    ("build", "Build the project"),
    ("test", "Run the test suite"),
    ("clean", "Remove build artifacts"),
]


def test_full_cycle_matches_ground_truth(tmp_path, monkeypatch):
    plugin = MakefileHelpPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for expected_target, expected_desc in EXPECTED:
        result = plugin.produce()
        assert result["target"] == expected_target
        assert result["description"] == expected_desc


def test_wraps_around(tmp_path, monkeypatch):
    plugin = MakefileHelpPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for _ in range(len(EXPECTED)):
        plugin.produce()
    result = plugin.produce()
    assert result["target"] == "build"
