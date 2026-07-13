import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)
from catalan_plugin import CatalanNumbersPlugin

KNOWN = [1, 1, 2, 5, 14, 42, 132, 429, 1430, 4862, 16796]

def test_sequence(tmp_path, monkeypatch):
    plugin = CatalanNumbersPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    got = [plugin.produce()["catalan"] for _ in range(len(KNOWN))]
    assert got == KNOWN
