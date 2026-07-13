import os
import sys
from pathlib import Path

import pytest

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from twin_primes_plugin import TwinPrimesPlugin


def test_is_prime():
    verified_true_for = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]
    verified_false_for = [1, 4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 20, 21, 22, 24, 25, 26, 27, 28]

    for n in verified_true_for:
        assert TwinPrimesPlugin()._is_prime(n) is True

    for n in verified_false_for:
        assert TwinPrimesPlugin()._is_prime(n) is False


def test_produce_no_exceptions(tmp_path, monkeypatch):
    plugin = TwinPrimesPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    for _ in range(15):
        plugin.produce()
