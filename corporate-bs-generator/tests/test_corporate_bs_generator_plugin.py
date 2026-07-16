import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from corporate_bs_generator_plugin import CorporateBsGeneratorPlugin


def test_first_4_ticks_cycle_adjectives_only(tmp_path, monkeypatch):
    plugin = CorporateBsGeneratorPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    sentences = []
    for _ in range(4):
        result = plugin.produce()
        sentences.append(result["sentence"])

    expected = [
        f"Let's leverage our {adj} paradigm."
        for adj in CorporateBsGeneratorPlugin._ADJECTIVES
    ]
    assert sentences == expected


def test_verb_changes_on_5th_tick(tmp_path, monkeypatch):
    plugin = CorporateBsGeneratorPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    for _ in range(4):
        plugin.produce()
    result = plugin.produce()
    assert "operationalize" in result["sentence"]
    assert "synergistic" in result["sentence"]
