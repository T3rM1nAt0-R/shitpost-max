import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from hyperloglog_estimator_plugin import HyperloglogEstimatorPlugin


def test_estimate_within_generous_error_after_one_full_pass(tmp_path, monkeypatch):
    plugin = HyperloglogEstimatorPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    stream_len = len(HyperloglogEstimatorPlugin._stream())
    result = None
    for _ in range(stream_len):
        result = plugin.produce()

    true_distinct = 300
    relative_error = abs(result["estimate"] - true_distinct) / true_distinct
    assert relative_error < 0.4


def test_estimate_is_always_positive(tmp_path, monkeypatch):
    plugin = HyperloglogEstimatorPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    for _ in range(30):
        result = plugin.produce()
        assert result["estimate"] > 0
