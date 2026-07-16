import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from unittest.mock import patch

from zero_shot_bench_plugin import _is_correct, ZeroShotBenchPlugin


def test_is_correct_true():
    assert _is_correct("The answer is 45.", "45") is True


def test_is_correct_false():
    assert _is_correct("I don't know", "45") is False


def test_running_counts_accumulate(tmp_path, monkeypatch):
    plugin = ZeroShotBenchPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    answers = iter(["45", "no idea", "63"])
    with patch("zero_shot_bench_plugin._call_ollama", side_effect=lambda p: next(answers)):
        r1 = plugin.produce()
        r2 = plugin.produce()
        r3 = plugin.produce()

    assert r1["correct"] is True
    assert r2["correct"] is False
    assert r3["correct"] is True
    assert r3["running_correct"] == 2
    assert r3["running_total"] == 3


def test_produce_returns_none_on_failure(tmp_path, monkeypatch):
    plugin = ZeroShotBenchPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    with patch("zero_shot_bench_plugin._call_ollama", side_effect=OSError("down")):
        assert plugin.produce() is None
