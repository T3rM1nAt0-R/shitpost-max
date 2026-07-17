import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from unittest.mock import patch

from few_shot_drift_plugin import _build_prompt, FewShotDriftPlugin


def test_build_prompt_zero_shot():
    assert _build_prompt(0) == "Text: The service was surprisingly good.\nSentiment:"


def test_build_prompt_two_shot():
    prompt = _build_prompt(2)
    assert "This movie was fantastic!" in prompt
    assert "I hated every minute of it." in prompt
    assert "It was okay, nothing special." not in prompt


def test_produce_returns_none_on_failure(tmp_path, monkeypatch):
    plugin = FewShotDriftPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    with patch("few_shot_drift_plugin._call_ollama", side_effect=OSError("down")):
        assert plugin.produce() is None
