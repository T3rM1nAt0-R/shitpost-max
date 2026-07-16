import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from mobius_function_plugin import MobiusFunctionPlugin

KNOWN_MOBIUS_1_10 = [1, -1, -1, 0, -1, 1, -1, 0, 0, 1]


def test_mobius_matches_known_values():
    plugin = MobiusFunctionPlugin()
    assert [plugin._mobius(n) for n in range(1, 11)] == KNOWN_MOBIUS_1_10


def test_produce_scans_consecutive_integers(tmp_path, monkeypatch):
    plugin = MobiusFunctionPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen_ns = []
    seen_mobius = []
    for _ in range(10):
        result = plugin.produce()
        seen_ns.append(result["n"])
        seen_mobius.append(result["mobius"])

    assert seen_ns == list(range(1, 11))
    assert seen_mobius == KNOWN_MOBIUS_1_10


def test_mobius_is_always_in_valid_range(tmp_path, monkeypatch):
    plugin = MobiusFunctionPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    for _ in range(60):
        result = plugin.produce()
        assert result["mobius"] in (-1, 0, 1)
