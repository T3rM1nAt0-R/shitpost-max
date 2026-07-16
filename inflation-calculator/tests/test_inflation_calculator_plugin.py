import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from inflation_calculator_plugin import InflationCalculatorPlugin


def test_year_0(tmp_path, monkeypatch):
    plugin = InflationCalculatorPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    result = plugin.produce()
    assert result["year"] == 0
    assert result["eroded_value"] == 100000.0


def test_year_10(tmp_path, monkeypatch):
    plugin = InflationCalculatorPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    result = None
    for _ in range(11):
        result = plugin.produce()
    assert result["year"] == 10
    assert result["eroded_value"] == 55839.48


def test_year_30_resets_to_year_0(tmp_path, monkeypatch):
    plugin = InflationCalculatorPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    result = None
    for _ in range(31):
        result = plugin.produce()
    assert result["year"] == 30
    assert result["eroded_value"] == 17411.01
    next_result = plugin.produce()
    assert next_result["year"] == 0
