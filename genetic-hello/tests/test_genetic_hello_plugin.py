import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from genetic_hello_plugin import GeneticHelloPlugin


def test_converges_to_target_by_generation_83(tmp_path, monkeypatch):
    plugin = GeneticHelloPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    result = None
    for _ in range(83):
        result = plugin.produce()

    assert result["current"] == "HI"
    assert result["fitness"] == 2


def test_fitness_is_monotonically_non_decreasing(tmp_path, monkeypatch):
    plugin = GeneticHelloPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    prev_fitness = 0
    for _ in range(83):
        result = plugin.produce()
        assert result["fitness"] >= prev_fitness
        prev_fitness = result["fitness"]
