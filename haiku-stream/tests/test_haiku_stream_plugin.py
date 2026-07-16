import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from haiku_stream_plugin import HaikuStreamPlugin


def test_cycles_through_all_haikus_in_order(tmp_path, monkeypatch):
    plugin = HaikuStreamPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen_indices = []
    for _ in range(10):
        result = plugin.produce()
        seen_indices.append(result["haiku_index"])

    assert seen_indices == [0, 1, 2, 3, 4, 0, 1, 2, 3, 4]


def test_haiku_text_matches_fixed_list(tmp_path, monkeypatch):
    plugin = HaikuStreamPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    result = plugin.produce()
    assert result["haiku"] == "\n".join(HaikuStreamPlugin._HAIKUS[0])
