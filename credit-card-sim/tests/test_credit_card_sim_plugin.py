import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from credit_card_sim_plugin import CreditCardSimPlugin


def test_month_1(tmp_path, monkeypatch):
    plugin = CreditCardSimPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    result = plugin.produce()
    assert result["cycle_month"] == 1
    assert result["balance_start"] == 5000.0
    assert result["interest"] == 100.0
    assert result["min_payment"] == 100.0
    assert result["balance_end"] == 5200.0


def test_month_24_resets_to_month_1(tmp_path, monkeypatch):
    plugin = CreditCardSimPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    result = None
    for _ in range(24):
        result = plugin.produce()
    assert result["cycle_month"] == 24
    assert result["balance_start"] == 9600.0
    assert result["balance_end"] == 9800.0
    next_result = plugin.produce()
    assert next_result["cycle_month"] == 1
    assert next_result["balance_start"] == 5000.0
