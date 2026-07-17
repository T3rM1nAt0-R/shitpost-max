import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from egyptian_fraction_plugin import EgyptianFractionPlugin

# Known-correct greedy Egyptian-fraction expansion of 4/17.
KNOWN_4_17_TERMS = [5, 29, 1233, 3039345]


def test_4_17_expansion_matches_known_terms(tmp_path, monkeypatch):
    plugin = EgyptianFractionPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    terms = []
    for _ in range(len(KNOWN_4_17_TERMS)):
        result = plugin.produce()
        assert result["rational"] == "4/17"
        terms.append(result["term_denominator"])

    assert terms == KNOWN_4_17_TERMS


def test_advances_to_next_rational_after_expansion_completes(tmp_path, monkeypatch):
    plugin = EgyptianFractionPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    for _ in range(len(KNOWN_4_17_TERMS)):
        plugin.produce()

    result = plugin.produce()
    assert result["rational"] == "5/21"
    assert result["term_index"] == 0


def test_term_denominators_are_always_positive_integers(tmp_path, monkeypatch):
    plugin = EgyptianFractionPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    for _ in range(30):
        result = plugin.produce()
        assert isinstance(result["term_denominator"], int)
        assert result["term_denominator"] > 0
