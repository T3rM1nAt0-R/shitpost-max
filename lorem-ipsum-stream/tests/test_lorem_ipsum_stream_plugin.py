import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from lorem_ipsum_stream_plugin import LoremIpsumStreamPlugin


def test_words_emitted_in_passage_order(tmp_path, monkeypatch):
    plugin = LoremIpsumStreamPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    n = len(LoremIpsumStreamPlugin._WORDS)
    seen = []
    for _ in range(n):
        result = plugin.produce()
        seen.append(result["word"])

    assert seen == LoremIpsumStreamPlugin._WORDS


def test_wraps_around_after_last_word(tmp_path, monkeypatch):
    plugin = LoremIpsumStreamPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    n = len(LoremIpsumStreamPlugin._WORDS)
    for _ in range(n):
        plugin.produce()

    result = plugin.produce()
    assert result["word"] == LoremIpsumStreamPlugin._WORDS[0]
