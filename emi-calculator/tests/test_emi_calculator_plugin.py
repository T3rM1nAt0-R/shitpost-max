import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from emi_calculator_plugin import EmiCalculatorPlugin

EXPECTED = [
    (200000, 0.09, 24, 9136.95),
    (500000, 0.085, 60, 10258.27),
    (1000000, 0.075, 120, 11870.18),
    (50000, 0.12, 12, 4442.44),
    (300000, 0.10, 36, 9680.16),
]


def test_full_cycle_matches_ground_truth(tmp_path, monkeypatch):
    plugin = EmiCalculatorPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for expected_principal, expected_rate, expected_tenure, expected_emi in EXPECTED:
        result = plugin.produce()
        assert result["principal"] == expected_principal
        assert result["annual_rate"] == expected_rate
        assert result["tenure_months"] == expected_tenure
        assert result["emi"] == expected_emi


def test_wraps_around(tmp_path, monkeypatch):
    plugin = EmiCalculatorPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for _ in range(len(EXPECTED)):
        plugin.produce()
    result = plugin.produce()
    assert result["principal"] == 200000
    assert result["emi"] == 9136.95
