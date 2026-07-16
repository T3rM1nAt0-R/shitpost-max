import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from loan_amortization_plugin import LoanAmortizationPlugin, PAYMENT


def test_payment_matches_ground_truth():
    assert round(PAYMENT, 2) == 10494.18


def test_month_1(tmp_path, monkeypatch):
    plugin = LoanAmortizationPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    result = plugin.produce()
    assert result["month"] == 1
    assert result["payment"] == 10494.18
    assert result["interest"] == 900.0
    assert result["principal_paid"] == 9594.18
    assert result["balance"] == 110405.82


def test_month_12_resets_to_month_1(tmp_path, monkeypatch):
    plugin = LoanAmortizationPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    result = None
    for _ in range(12):
        result = plugin.produce()
    assert result["month"] == 12
    assert result["balance"] == 0.0
    next_result = plugin.produce()
    assert next_result["month"] == 1
