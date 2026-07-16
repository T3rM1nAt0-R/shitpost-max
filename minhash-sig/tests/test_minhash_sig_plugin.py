import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from minhash_sig_plugin import MinhashSigPlugin


def test_true_jaccard_is_half(tmp_path, monkeypatch):
    plugin = MinhashSigPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    result = plugin.produce()
    assert result["true_jaccard"] == 0.5


def test_estimate_in_valid_range(tmp_path, monkeypatch):
    plugin = MinhashSigPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    for _ in range(10):
        result = plugin.produce()
        assert 0.0 <= result["estimated_jaccard"] <= 1.0


def test_identical_sets_give_estimate_of_one():
    plugin = MinhashSigPlugin()
    s = {"x", "y", "z"}
    sig_a = plugin._minhash_signature(s)
    sig_b = plugin._minhash_signature(s)
    assert plugin._estimate_jaccard(sig_a, sig_b) == 1.0
