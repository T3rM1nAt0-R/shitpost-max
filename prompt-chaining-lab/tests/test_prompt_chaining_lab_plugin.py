import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from unittest.mock import patch

from prompt_chaining_lab_plugin import PromptChainingLabPlugin, TOPICS


def test_chain_wiring_and_cycling(tmp_path, monkeypatch):
    plugin = PromptChainingLabPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    calls = []

    def fake_call(prompt, num_predict=None):
        calls.append(prompt)
        if len(calls) % 2 == 1:
            return "Stage one output text."
        return "three word summary"

    with patch("prompt_chaining_lab_plugin._call_ollama", side_effect=fake_call):
        result = plugin.produce()

    assert result["topic"] == TOPICS[0]
    assert result["stage1_output"] == "Stage one output text."
    assert result["stage2_output"] == "three word summary"
    # stage 2's prompt must embed stage 1's exact output
    assert "Stage one output text." in calls[1]


def test_produce_returns_none_on_failure(tmp_path, monkeypatch):
    plugin = PromptChainingLabPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    with patch("prompt_chaining_lab_plugin._call_ollama", side_effect=OSError("down")):
        assert plugin.produce() is None
