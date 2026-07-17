import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

import pytest
from unittest.mock import patch

from sentiment_drift_plugin import _parse_score, _update_stats, SentimentDriftPlugin


def test_update_stats_matches_ground_truth():
    state = {"n": 0, "mean": 0.0, "m2": 0.0, "variance": 0.0}
    for score, expected_mean, expected_var in [
        (8, 8.0, 0.0),
        (6, 7.0, 1.0),
        (9, 7.666666666666667, 1.5555555555555554),
        (7, 7.5, 1.25),
    ]:
        state = _update_stats(state, score)
        assert state["mean"] == pytest.approx(expected_mean)
        assert state["variance"] == pytest.approx(expected_var)


def test_parse_score_valid():
    assert _parse_score("I'd say 8 out of 10.") == 8


def test_parse_score_invalid_raises():
    with pytest.raises(ValueError):
        _parse_score("no numbers here at all")


def test_produce_returns_none_on_failure(tmp_path, monkeypatch):
    plugin = SentimentDriftPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    with patch("sentiment_drift_plugin._call_ollama", side_effect=OSError("down")):
        assert plugin.produce() is None
