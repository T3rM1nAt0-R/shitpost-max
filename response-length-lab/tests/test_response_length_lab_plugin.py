import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from unittest.mock import patch

from response_length_lab_plugin import _measure, ResponseLengthLabPlugin


def test_measure_matches_ground_truth():
    assert _measure("The robot painted slowly.") == {"char_count": 25, "word_count": 4}


def test_measure_empty_string():
    assert _measure("") == {"char_count": 0, "word_count": 0}


def test_produce_returns_none_on_failure(tmp_path, monkeypatch):
    plugin = ResponseLengthLabPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    with patch("response_length_lab_plugin._call_ollama", side_effect=OSError("down")):
        assert plugin.produce() is None
