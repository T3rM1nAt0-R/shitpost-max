import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from sieving_sundaram_plugin import SievingSundaramPlugin

KNOWN_PRIMES_15 = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]


def test_sundaram_primes_matches_known_sequence():
    plugin = SievingSundaramPlugin()
    assert plugin._sundaram_primes(15) == KNOWN_PRIMES_15


def test_emits_primes_in_order(tmp_path, monkeypatch):
    plugin = SievingSundaramPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    found = []
    for _ in range(11):
        result = plugin.produce()
        found.append(result["prime"])

    assert found == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]


def test_grows_sieve_when_exhausted(tmp_path, monkeypatch):
    plugin = SievingSundaramPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    found = []
    for _ in range(30):
        result = plugin.produce()
        found.append(result["prime"])

    assert found == sorted(found)
    assert len(set(found)) == len(found)
