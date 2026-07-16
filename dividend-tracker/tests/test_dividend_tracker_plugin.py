import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from dividend_tracker_plugin import DividendTrackerPlugin

EXPECTED = [
    ("AAPL", 0.225),
    ("MSFT", 0.735),
    ("JNJ", 1.1625),
    ("KO", 0.4805),
    ("PG", 0.99),
    ("XOM", 0.9488),
]


def test_full_cycle_matches_ground_truth(tmp_path, monkeypatch):
    plugin = DividendTrackerPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for expected_ticker, expected_payout in EXPECTED:
        result = plugin.produce()
        assert result["ticker"] == expected_ticker
        assert result["quarterly_payout"] == expected_payout


def test_wraps_around(tmp_path, monkeypatch):
    plugin = DividendTrackerPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for _ in range(len(EXPECTED)):
        plugin.produce()
    result = plugin.produce()
    assert result["ticker"] == "AAPL"
    assert result["quarterly_payout"] == 0.225
