import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)
from primes_plugin import PrimesForeverPlugin

KNOWN = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]

def test_sequence(tmp_path, monkeypatch):
    plugin = PrimesForeverPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    got = [plugin.produce()["prime"] for _ in range(len(KNOWN))]
    assert got == KNOWN
