import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from babylonian_sqrt_plugin import BabylonianSqrtPlugin


def test_converges_to_sqrt2_within_6_iterations(tmp_path, monkeypatch):
    plugin = BabylonianSqrtPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    last_for_n2 = None
    for _ in range(6):
        result = plugin.produce()
        if result["n"] != 2:
            break
        last_for_n2 = result

    assert abs(last_for_n2["approximation"] - 1.4142135623730951) < 1e-6


def test_never_targets_a_perfect_square(tmp_path, monkeypatch):
    plugin = BabylonianSqrtPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen_targets = set()
    for _ in range(200):
        result = plugin.produce()
        seen_targets.add(result["n"])

    for n in seen_targets:
        root = int(n ** 0.5)
        assert root * root != n, f"{n} is a perfect square"


def test_advances_to_next_target_after_convergence(tmp_path, monkeypatch):
    plugin = BabylonianSqrtPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen_ns = []
    for _ in range(60):
        result = plugin.produce()
        if result["n"] not in seen_ns:
            seen_ns.append(result["n"])

    assert seen_ns[:3] == [2, 3, 5]
