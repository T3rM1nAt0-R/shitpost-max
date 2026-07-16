import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from fd_calculator_plugin import FdCalculatorPlugin

EXPECTED = [
    (1, 53592.95),
    (2, 57444.09),
    (3, 61571.97),
    (5, 70738.91),
    (10, 100079.87),
]


def test_full_cycle_matches_ground_truth(tmp_path, monkeypatch):
    plugin = FdCalculatorPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for expected_years, expected_maturity in EXPECTED:
        result = plugin.produce()
        assert result["tenure_years"] == expected_years
        assert result["maturity_amount"] == expected_maturity


def test_wraps_around(tmp_path, monkeypatch):
    plugin = FdCalculatorPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for _ in range(len(EXPECTED)):
        plugin.produce()
    result = plugin.produce()
    assert result["tenure_years"] == 1
    assert result["maturity_amount"] == 53592.95
