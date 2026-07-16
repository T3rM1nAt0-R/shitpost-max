import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from lumpsum_calculator_plugin import LumpsumCalculatorPlugin

EXPECTED = [
    (0, 100000.0),
    (1, 110000.0),
    (5, 161051.0),
    (10, 259374.25),
    (20, 672749.99),
]


def test_full_cycle_matches_ground_truth(tmp_path, monkeypatch):
    plugin = LumpsumCalculatorPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for expected_year, expected_fv in EXPECTED:
        result = plugin.produce()
        assert result["year"] == expected_year
        assert result["future_value"] == expected_fv


def test_wraps_around(tmp_path, monkeypatch):
    plugin = LumpsumCalculatorPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for _ in range(len(EXPECTED)):
        plugin.produce()
    result = plugin.produce()
    assert result["year"] == 0
    assert result["future_value"] == 100000.0
