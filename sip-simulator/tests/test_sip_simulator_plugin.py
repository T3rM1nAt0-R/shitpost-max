import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from sip_simulator_plugin import SipSimulatorPlugin


def test_month_1(tmp_path, monkeypatch):
    plugin = SipSimulatorPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    result = plugin.produce()
    assert result["month"] == 1
    assert result["monthly_return"] == 0.01
    assert result["corpus"] == 5000.0
    assert result["invested"] == 5000.0


def test_month_12(tmp_path, monkeypatch):
    plugin = SipSimulatorPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    result = None
    for _ in range(12):
        result = plugin.produce()
    assert result["month"] == 12
    assert result["corpus"] == 62476.56
    assert result["invested"] == 60000.0


def test_month_36_resets_to_month_1(tmp_path, monkeypatch):
    plugin = SipSimulatorPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    result = None
    for _ in range(36):
        result = plugin.produce()
    assert result["month"] == 36
    assert result["corpus"] == 204252.93
    assert result["invested"] == 180000.0
    next_result = plugin.produce()
    assert next_result["month"] == 1
    assert next_result["corpus"] == 5000.0
    assert next_result["invested"] == 5000.0
