import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from conway_life_plugin import ConwayLifePlugin


def test_blinker_oscillates_with_period_2():
    initial = ConwayLifePlugin._initial_grid()
    gen1 = ConwayLifePlugin._step(initial)
    gen2 = ConwayLifePlugin._step(gen1)

    assert sum(sum(row) for row in gen1) == 3
    assert sum(sum(row) for row in gen2) == 3
    assert gen2 == initial


def test_produce_always_reports_three_live_cells(tmp_path, monkeypatch):
    plugin = ConwayLifePlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    for i in range(10):
        result = plugin.produce()
        assert result["generation"] == i + 1
        assert result["live_cells"] == 3
