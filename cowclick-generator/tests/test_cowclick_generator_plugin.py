import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from cowclick_generator_plugin import CowclickGeneratorPlugin


def test_cycles_through_all_messages_in_order(tmp_path, monkeypatch):
    plugin = CowclickGeneratorPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen = []
    for _ in range(5):
        result = plugin.produce()
        seen.append(result["message"])

    assert seen == CowclickGeneratorPlugin._MESSAGES


def test_message_appears_in_its_own_art(tmp_path, monkeypatch):
    plugin = CowclickGeneratorPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    for _ in range(5):
        result = plugin.produce()
        assert result["message"] in result["art"]
