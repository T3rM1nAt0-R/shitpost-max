import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from aliquot_sequences_plugin import _aliquot_sum, _sequence

EXPECTED = [
    (12, [12, 16, 15, 9, 4, 3, 1, 0], "terminated"),
    (6, [6, 6], "cycle"),
    (220, [220, 284, 220], "cycle"),
    (25, [25, 6, 6], "cycle"),
    (95, [95, 25, 6, 6], "cycle"),
]


def test_sequence_matches_ground_truth():
    for start, expected_seq, expected_status in EXPECTED:
        seq, status = _sequence(start)
        assert seq == expected_seq
        assert status == expected_status


def test_diverged_status(monkeypatch):
    import aliquot_sequences_plugin as mod
    monkeypatch.setattr(mod, "_aliquot_sum", lambda n: 10 ** 9)
    seq, status = mod._sequence(5)
    assert status == "diverged"


def test_max_steps_reached_status(monkeypatch):
    import aliquot_sequences_plugin as mod
    counter = {"n": 100}

    def fake_sum(n):
        counter["n"] += 1
        return counter["n"]

    monkeypatch.setattr(mod, "_aliquot_sum", fake_sum)
    seq, status = mod._sequence(1)
    assert status == "max_steps_reached"
    assert len(seq) == mod.MAX_STEPS + 1
