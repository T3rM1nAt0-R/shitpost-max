import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

import pytest
from unittest.mock import patch

from llm_self_eval_plugin import _parse_rating, LlmSelfEvalPlugin


def test_parse_rating_valid():
    assert _parse_rating("I would rate this an 8 out of 10.") == 8


def test_parse_rating_invalid_raises():
    with pytest.raises(ValueError):
        _parse_rating("no numbers here")


def test_running_average_accumulates(tmp_path, monkeypatch):
    plugin = LlmSelfEvalPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    responses = iter(["answer1", "8", "answer2", "6", "answer3", "9"])
    with patch("llm_self_eval_plugin._call_ollama", side_effect=lambda p: next(responses)):
        r1 = plugin.produce()
        r2 = plugin.produce()
        r3 = plugin.produce()

    assert r1["self_rating"] == 8
    assert r2["self_rating"] == 6
    assert r3["self_rating"] == 9
    assert r3["sample_count"] == 3
    assert r3["running_avg_rating"] == round((8 + 6 + 9) / 3, 2)


def test_produce_returns_none_on_failure(tmp_path, monkeypatch):
    plugin = LlmSelfEvalPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    with patch("llm_self_eval_plugin._call_ollama", side_effect=OSError("down")):
        assert plugin.produce() is None
