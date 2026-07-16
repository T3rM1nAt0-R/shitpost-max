import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from unittest.mock import patch

from logprobs_tracker_plugin import _normalize, _agreement_fraction, LogprobsTrackerPlugin


def test_agreement_fraction_partial():
    assert _agreement_fraction(["Tokyo", "Tokyo", "Osaka"]) == 2 / 3


def test_agreement_fraction_full():
    assert _agreement_fraction(["Tokyo.", "tokyo", "TOKYO"]) == 1.0


def test_running_average_accumulates(tmp_path, monkeypatch):
    plugin = LogprobsTrackerPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    call_batches = iter([
        ["Tokyo", "Tokyo", "Tokyo"],  # confidence 1.0
        ["Tokyo", "Osaka", "Kyoto"],  # confidence 1/3
    ])

    def fake_call(prompt):
        batch = current_batch[0]
        return batch.pop(0)

    for expected_conf in [1.0, 1 / 3]:
        batch = next(call_batches)
        current_batch = [batch]
        with patch("logprobs_tracker_plugin._call_ollama", side_effect=fake_call):
            result = plugin.produce()
        assert result["confidence"] == round(expected_conf, 2)

    assert result["sample_count"] == 2
    assert result["running_avg_confidence"] == round((1.0 + 1 / 3) / 2, 4)


def test_produce_returns_none_on_failure(tmp_path, monkeypatch):
    plugin = LogprobsTrackerPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    with patch("logprobs_tracker_plugin._call_ollama", side_effect=OSError("down")):
        assert plugin.produce() is None
