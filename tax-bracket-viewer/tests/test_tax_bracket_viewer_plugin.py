import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from tax_bracket_viewer_plugin import TaxBracketViewerPlugin

EXPECTED = [
    (250000, 0.0, 0.0),
    (500000, 10000.0, 0.05),
    (900000, 40000.0, 0.10),
    (1100000, 65000.0, 0.15),
    (1400000, 120000.0, 0.20),
    (2000000, 290000.0, 0.30),
]


def test_full_cycle_matches_ground_truth(tmp_path, monkeypatch):
    plugin = TaxBracketViewerPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for expected_income, expected_liability, expected_rate in EXPECTED:
        result = plugin.produce()
        assert result["income"] == expected_income
        assert result["liability"] == expected_liability
        assert result["marginal_rate"] == expected_rate


def test_wraps_around(tmp_path, monkeypatch):
    plugin = TaxBracketViewerPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for _ in range(len(EXPECTED)):
        plugin.produce()
    result = plugin.produce()
    assert result["income"] == 250000
    assert result["liability"] == 0.0
