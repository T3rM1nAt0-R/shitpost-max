import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from multiplicative_persistence_plugin import MultiplicativePersistencePlugin

KNOWN_PERSISTENCE_0_15 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1]


def test_persistence_matches_known_values():
    plugin = MultiplicativePersistencePlugin()
    assert [plugin._persistence(n) for n in range(16)] == KNOWN_PERSISTENCE_0_15
    assert plugin._persistence(39) == 3
    assert plugin._persistence(77) == 4
    assert plugin._persistence(679) == 5


def test_produce_scans_consecutive_integers(tmp_path, monkeypatch):
    plugin = MultiplicativePersistencePlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen_ns = []
    seen_persistences = []
    for _ in range(16):
        result = plugin.produce()
        seen_ns.append(result["n"])
        seen_persistences.append(result["persistence"])

    assert seen_ns == list(range(16))
    assert seen_persistences == KNOWN_PERSISTENCE_0_15


def test_every_tick_produces_a_result(tmp_path, monkeypatch):
    plugin = MultiplicativePersistencePlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    for _ in range(50):
        assert plugin.produce() is not None
