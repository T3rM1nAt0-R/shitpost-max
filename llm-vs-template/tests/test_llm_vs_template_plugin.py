import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from unittest.mock import patch

from llm_vs_template_plugin import _jaccard, LlmVsTemplatePlugin


def test_jaccard_matches_ground_truth():
    result = _jaccard("the cat sat on the mat", "the cat sat on a rug")
    assert round(result, 3) == 0.571


def test_jaccard_empty_strings():
    assert _jaccard("", "") == 0.0


def test_produce_returns_none_on_failure(tmp_path, monkeypatch):
    plugin = LlmVsTemplatePlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    with patch("llm_vs_template_plugin._call_ollama", side_effect=OSError("down")):
        assert plugin.produce() is None
