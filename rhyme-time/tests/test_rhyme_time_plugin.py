import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from rhyme_time_plugin import RhymeTimePlugin


def test_cycles_through_all_words_in_order(tmp_path, monkeypatch):
    plugin = RhymeTimePlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen = []
    for _ in range(6):
        result = plugin.produce()
        seen.append((result["word"], result["rhymes"]))

    expected = [(w, RhymeTimePlugin._RHYMES[w]) for w in RhymeTimePlugin._WORDS]
    assert seen == expected
