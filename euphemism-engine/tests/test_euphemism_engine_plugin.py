import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from euphemism_engine_plugin import EuphemismEnginePlugin


def test_cycles_through_all_pairs_in_order(tmp_path, monkeypatch):
    plugin = EuphemismEnginePlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen = []
    for _ in range(6):
        result = plugin.produce()
        seen.append((result["blunt"], result["euphemism"]))

    assert seen == EuphemismEnginePlugin._PAIRS
