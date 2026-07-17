import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from look_and_say_plugin import _next_term, LookAndSayPlugin, MAX_TERMS

EXPECTED_FIRST_SIX = ["1", "11", "21", "1211", "111221", "312211"]
TERM_14 = "311311222113111231131112132112311321322112111312211312111322212311322113212221"


def test_next_term_matches_ground_truth():
    term = "1"
    terms = [term]
    for _ in range(5):
        term = _next_term(term)
        terms.append(term)
    assert terms == EXPECTED_FIRST_SIX


def test_term_14_exact():
    term = "1"
    for _ in range(14):
        term = _next_term(term)
    assert term == TERM_14
    assert len(term) == 78


def test_full_cycle_and_reset(tmp_path, monkeypatch):
    plugin = LookAndSayPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    result = plugin.produce()
    assert result["term_index"] == 0
    assert result["term"] == "1"

    for _ in range(MAX_TERMS - 1):
        result = plugin.produce()
    assert result["term_index"] == MAX_TERMS - 1
    assert result["term"] == TERM_14
    assert result["term_length"] == 78

    next_result = plugin.produce()
    assert next_result["term_index"] == 0
    assert next_result["term"] == "1"
