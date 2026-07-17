import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from epidemic_sim_plugin import EpidemicSimPlugin

KNOWN = [
    (987.03, 11.97, 1.0), (983.49, 14.32, 2.2), (979.26, 17.11, 3.63),
    (974.23, 20.43, 5.34), (968.26, 24.35, 7.38), (961.19, 28.99, 9.82),
    (952.83, 34.45, 12.72), (942.98, 40.86, 16.16), (931.43, 48.33, 20.25),
    (917.92, 57.0, 25.08),
]


def test_10_days_match_known_sequence(tmp_path, monkeypatch):
    plugin = EpidemicSimPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen = []
    for _ in range(10):
        result = plugin.produce()
        seen.append((result["s"], result["i"], result["r"]))

    assert seen == KNOWN


def test_population_is_conserved(tmp_path, monkeypatch):
    plugin = EpidemicSimPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    for _ in range(20):
        result = plugin.produce()
        total = result["s"] + result["i"] + result["r"]
        assert abs(total - 1000) < 0.5
