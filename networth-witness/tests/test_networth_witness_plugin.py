import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from unittest.mock import patch, MagicMock

from networth_witness_plugin import _commit_count, FAKE_NET_WORTH_MULTIPLIER, NetWorthWitnessPlugin


def _fake_git_result(stdout="", returncode=0):
    result = MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    return result


def test_commit_count_matches_ground_truth():
    with patch("subprocess.run", return_value=_fake_git_result(stdout="149843\n")):
        assert _commit_count("/fake/repo") == 149843


def test_commit_count_returns_none_on_git_failure():
    with patch("subprocess.run", return_value=_fake_git_result(returncode=1)):
        assert _commit_count("/fake/repo") is None


def test_commit_count_returns_none_on_malformed_output():
    with patch("subprocess.run", return_value=_fake_git_result(stdout="not a number\n")):
        assert _commit_count("/fake/repo") is None


def test_commit_count_returns_none_when_git_missing():
    with patch("subprocess.run", side_effect=FileNotFoundError("git not found")):
        assert _commit_count("/fake/repo") is None


def test_produce_computes_fake_net_worth_matching_ground_truth(tmp_path, monkeypatch):
    plugin = NetWorthWitnessPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    with patch("networth_witness_plugin._commit_count", return_value=149843):
        result = plugin.produce()

    assert result["commit_count"] == 149843
    assert result["net_worth_sc"] == 149843 * FAKE_NET_WORTH_MULTIPLIER
    assert result["net_worth_sc"] == 14_984_300_000_000
    assert result["entry_count"] == 1


def test_produce_returns_none_when_commit_count_unavailable(tmp_path, monkeypatch):
    plugin = NetWorthWitnessPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    with patch("networth_witness_plugin._commit_count", return_value=None):
        assert plugin.produce() is None


def test_history_accumulates_across_ticks(tmp_path, monkeypatch):
    plugin = NetWorthWitnessPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    with patch("networth_witness_plugin._commit_count", side_effect=[100, 101, 102]):
        for expected_count in (1, 2, 3):
            result = plugin.produce()
            assert result["entry_count"] == expected_count
