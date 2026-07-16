import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from fermat_factor_plugin import FermatFactorPlugin


def test_fermat_factor_matches_known_values():
    plugin = FermatFactorPlugin()
    assert plugin._fermat_factor(5959) == (59, 101)
    assert plugin._fermat_factor(8051) == (83, 97)
    assert plugin._fermat_factor(15) == (3, 5)
    assert plugin._fermat_factor(21) == (3, 7)


def test_produce_skips_primes_and_factors_composites(tmp_path, monkeypatch):
    plugin = FermatFactorPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    ns_seen = []
    for _ in range(3):
        result = plugin.produce()
        ns_seen.append(result["n"])
        assert result["factor1"] * result["factor2"] == result["n"]

    assert ns_seen == [15, 21, 25]
