import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from equilibrium_drift_plugin import (
    EquilibriumDriftPlugin, _lcg_next, _first_return_time, _update_running_mean,
    _windowed_median, SEED, CAP, WINDOW_SIZE,
)

EXPECTED_RETURN_TIMES = [6, 2, 18, 6, 18, 2, 66, 1912, 34, 2, 2, 2, 2, 160, 4, 4, 2, 2, 6, 6820]


def test_first_20_trials_match_ground_truth(tmp_path, monkeypatch):
    plugin = EquilibriumDriftPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    results = []
    for _ in range(20):
        results.append(plugin.produce())

    assert [r["return_time"] for r in results] == EXPECTED_RETURN_TIMES
    assert all(r["capped"] is False for r in results)

    assert results[0]["running_mean"] == 6.0
    assert results[7]["running_mean"] == 253.75
    assert results[19]["running_mean"] == 453.5

    assert results[0]["windowed_median"] == 6
    assert results[7]["windowed_median"] == 12.0
    assert results[19]["windowed_median"] == 5.0


def test_capped_path():
    # A cap of 1 with a seed that won't return within 1 toss must report capped.
    lcg_state, return_time, capped = _first_return_time(SEED, cap=1)
    assert capped is True
    assert return_time == 1


def test_window_evicts_beyond_window_size(tmp_path, monkeypatch):
    plugin = EquilibriumDriftPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    for _ in range(WINDOW_SIZE + 10):
        plugin.produce()

    state = plugin._load_persisted_state({
        "lcg_state": SEED, "trial_count": 0, "running_sum": 0, "window": [],
    })
    assert len(state["window"]) == WINDOW_SIZE


def test_update_running_mean_pure():
    count, total, mean = _update_running_mean(0, 0, 6)
    assert (count, total, mean) == (1, 6, 6.0)
    count, total, mean = _update_running_mean(1, 6, 2)
    assert (count, total, mean) == (2, 8, 4.0)


def test_windowed_median_odd_and_even():
    assert _windowed_median([3, 1, 2]) == 2
    assert _windowed_median([1, 2, 3, 4]) == 2.5


def test_lcg_next_deterministic():
    s1, u1 = _lcg_next(SEED)
    s2, u2 = _lcg_next(SEED)
    assert (s1, u1) == (s2, u2)
