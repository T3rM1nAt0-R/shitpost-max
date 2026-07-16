import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from continued_fraction_plugin import ContinuedFractionPlugin

KNOWN_SQRT2_TERMS = [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]


def test_sqrt2_terms_match_known_sequence(tmp_path, monkeypatch):
    plugin = ContinuedFractionPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    terms = []
    for _ in range(len(KNOWN_SQRT2_TERMS)):
        result = plugin.produce()
        assert result["constant"] == "sqrt(2)"
        terms.append(result["term"])

    assert terms == KNOWN_SQRT2_TERMS


def test_advances_to_next_constant_after_term_cap(tmp_path, monkeypatch):
    plugin = ContinuedFractionPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    for _ in range(len(KNOWN_SQRT2_TERMS)):
        plugin.produce()

    result = plugin.produce()
    assert result["constant"] == "sqrt(3)"
    assert result["term_index"] == 0


def test_all_terms_are_nonnegative_integers(tmp_path, monkeypatch):
    plugin = ContinuedFractionPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    for _ in range(50):
        result = plugin.produce()
        assert isinstance(result["term"], int)
        assert result["term"] >= 0
