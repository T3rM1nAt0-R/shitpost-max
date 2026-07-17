import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from retirement_sim_plugin import RetirementSimPlugin


def test_month_1(tmp_path, monkeypatch):
    plugin = RetirementSimPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    result = plugin.produce()
    assert result["month"] == 1
    assert result["corpus"] == 10000.0
    assert result["target_reached"] is False


def test_month_74_reaches_target_then_resets(tmp_path, monkeypatch):
    plugin = RetirementSimPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    result = None
    for _ in range(74):
        result = plugin.produce()
    assert result["month"] == 74
    assert result["corpus"] == 1017616.49
    assert result["target_reached"] is True

    next_result = plugin.produce()
    assert next_result["month"] == 1
    assert next_result["corpus"] == 10000.0
    assert next_result["target_reached"] is False
