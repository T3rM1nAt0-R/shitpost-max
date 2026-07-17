import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from config_validator_plugin import ConfigValidatorPlugin

EXPECTED = [
    ("config.json", True),
    ("broken.json", False),
    ("pyproject.toml", True),
    ("broken.toml", False),
    ("settings.yaml", True),
    ("broken.yaml", False),
]


def test_full_cycle_matches_ground_truth(tmp_path, monkeypatch):
    plugin = ConfigValidatorPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for expected_name, expected_valid in EXPECTED:
        result = plugin.produce()
        assert result["filename"] == expected_name
        assert result["is_valid"] == expected_valid
        if expected_valid:
            assert result["error"] is None
        else:
            assert result["error"] is not None


def test_wraps_around(tmp_path, monkeypatch):
    plugin = ConfigValidatorPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for _ in range(len(EXPECTED)):
        plugin.produce()
    result = plugin.produce()
    assert result["filename"] == "config.json"
    assert result["is_valid"] is True
