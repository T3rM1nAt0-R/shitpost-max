import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)
from pascal_plugin import PascalRowPlugin

KNOWN = [[1], [1,1], [1,2,1], [1,3,3,1], [1,4,6,4,1], [1,5,10,10,5,1]]

def test_sequence(tmp_path, monkeypatch):
    plugin = PascalRowPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    got = [plugin.produce()["row"] for _ in range(len(KNOWN))]
    assert got == KNOWN
