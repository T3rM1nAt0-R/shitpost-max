import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from acronym_expander_plugin import AcronymExpanderPlugin


def test_cycles_through_all_pairs_in_order(tmp_path, monkeypatch):
    plugin = AcronymExpanderPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen = []
    for _ in range(8):
        result = plugin.produce()
        seen.append(result["acronym"])

    expected = [p[0] for p in AcronymExpanderPlugin._PAIRS]
    assert seen == expected + expected[:2]
