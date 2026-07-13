import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)
from sqrt2_spigot import Sqrt2SpigotPlugin

KNOWN = [1,4,1,4,2,1,3,5,6,2,3,7,3,0,9]

def test_sequence(tmp_path, monkeypatch):
    plugin = Sqrt2SpigotPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    got = [plugin.produce()["digit"] for _ in range(len(KNOWN))]
    assert got == KNOWN
