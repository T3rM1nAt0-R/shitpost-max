import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from unittest.mock import patch

from prompt_template_lab_plugin import _fill, PromptTemplateLabPlugin


def test_fill_matches_ground_truth():
    assert _fill("melancholy", "autumn leaves") == "Write a melancholy haiku about autumn leaves."
    assert _fill("joyful", "a new puppy") == "Write a joyful haiku about a new puppy."
    assert _fill("mysterious", "an old library") == "Write a mysterious haiku about an old library."
    assert _fill("energetic", "a thunderstorm") == "Write a energetic haiku about a thunderstorm."
    assert _fill("peaceful", "a quiet lake") == "Write a peaceful haiku about a quiet lake."


def test_produce_returns_none_on_failure(tmp_path, monkeypatch):
    plugin = PromptTemplateLabPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    with patch("prompt_template_lab_plugin._call_ollama", side_effect=OSError("down")):
        assert plugin.produce() is None
