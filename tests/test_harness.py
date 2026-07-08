import fcntl
import json
import os
import shutil
import subprocess
import tempfile
from unittest.mock import patch

import pytest

from harness.shitpost_base import Shitpost


class FakeShitpost(Shitpost):
    """A test-double plugin whose output is injected at construction."""

    name = "fake"
    internal = False
    commit_template = "tick: {value}"

    def __init__(self, output, plugin_dir):
        self._output = output
        self._plugin_dir_override = plugin_dir

    def produce(self):
        return self._output

    def _plugin_dir(self):
        return self._plugin_dir_override


def _read_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def test_run_tick_writes_state_and_summary_and_commits():
    with tempfile.TemporaryDirectory() as tmp:
        fake = FakeShitpost({"value": 42}, tmp)

        with patch.object(fake, "_git_commit_push") as mock_commit:
            fake.run_tick()

        state = _read_jsonl(os.path.join(tmp, "state.jsonl"))
        assert len(state) == 1
        assert state[0]["value"] == 42
        assert "timestamp" in state[0]

        with open(os.path.join(tmp, "summary.json"), encoding="utf-8") as f:
            summary = json.load(f)
        assert summary == {"value": 42}

        mock_commit.assert_called_once_with("tick: 42")


def test_run_tick_none_skip_does_nothing():
    with tempfile.TemporaryDirectory() as tmp:
        fake = FakeShitpost(None, tmp)

        with patch.object(fake, "_git_commit_push") as mock_commit:
            fake.run_tick()

        assert not os.path.exists(os.path.join(tmp, "state.jsonl"))
        assert not os.path.exists(os.path.join(tmp, "summary.json"))
        mock_commit.assert_not_called()


def test_run_tick_exception_is_isolated():
    class BrokenShitpost(Shitpost):
        name = "broken"
        internal = True
        commit_template = "broken: {value}"

        def __init__(self, plugin_dir):
            self._plugin_dir_override = plugin_dir

        def produce(self):
            raise ValueError("intentional test failure")

        def _plugin_dir(self):
            return self._plugin_dir_override

    with tempfile.TemporaryDirectory() as tmp:
        broken = BrokenShitpost(tmp)

        with patch.object(broken, "_git_commit_push") as mock_commit:
            broken.run_tick()

        state = _read_jsonl(os.path.join(tmp, "state.jsonl"))
        assert len(state) == 1
        assert "error" in state[0]
        assert "ValueError" in state[0]["error"]
        assert "intentional test failure" in state[0]["error"]

        assert not os.path.exists(os.path.join(tmp, "summary.json"))
        mock_commit.assert_not_called()


def test_run_tick_multi_line_format():
    with tempfile.TemporaryDirectory() as tmp:
        fake = FakeShitpost(
            ({"value": "two-things", "count": 2}, [{"item": "a"}, {"item": "b"}]),
            tmp,
        )
        fake.commit_template = "{value}: {count}"

        with patch.object(fake, "_git_commit_push") as mock_commit:
            fake.run_tick()

        state = _read_jsonl(os.path.join(tmp, "state.jsonl"))
        assert len(state) == 2
        assert state[0]["item"] == "a"
        assert state[1]["item"] == "b"
        assert state[0]["timestamp"] == state[1]["timestamp"]

        with open(os.path.join(tmp, "summary.json"), encoding="utf-8") as f:
            summary = json.load(f)
        assert summary == {"value": "two-things", "count": 2}

        mock_commit.assert_called_once_with("two-things: 2")


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_run_tick_git_commit_push_integration():
    """A real git repo commits successfully; a missing remote is isolated."""
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["git", "init"], cwd=tmp, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "--local", "user.name", "Test User"],
            cwd=tmp,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "--local", "user.email", "test@example.com"],
            cwd=tmp,
            check=True,
            capture_output=True,
        )

        fake = FakeShitpost({"value": 123}, tmp)
        fake.run_tick()  # push fails (no remote), but must not raise.

        state = _read_jsonl(os.path.join(tmp, "state.jsonl"))
        assert len(state) == 1
        assert state[0]["value"] == 123

        log = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            cwd=tmp,
            check=True,
            capture_output=True,
            text=True,
        )
        assert "tick: 123" in log.stdout


def test_run_tick_commit_template_key_error_is_isolated():
    """A bad commit_template referencing a missing key must not crash the tick."""
    with tempfile.TemporaryDirectory() as tmp:
        fake = FakeShitpost({"value": 42}, tmp)
        fake.commit_template = "tick: {missing}"

        with patch.object(fake, "_git_commit_push") as mock_commit:
            fake.run_tick()

        state = _read_jsonl(os.path.join(tmp, "state.jsonl"))
        assert len(state) == 2
        assert state[0]["value"] == 42
        assert "error" in state[1]
        assert "KeyError" in state[1]["error"]
        assert "missing" in state[1]["error"]
        mock_commit.assert_not_called()


def test_run_tick_tuple_wrong_length_is_isolated():
    with tempfile.TemporaryDirectory() as tmp:
        fake = FakeShitpost(({"value": 1}, [{"item": "a"}], "extra"), tmp)

        with patch.object(fake, "_git_commit_push") as mock_commit:
            fake.run_tick()

        state = _read_jsonl(os.path.join(tmp, "state.jsonl"))
        assert len(state) == 1
        assert "error" in state[0]
        assert "tuple of length 3" in state[0]["error"]
        mock_commit.assert_not_called()


def test_run_tick_details_non_dict_is_isolated():
    with tempfile.TemporaryDirectory() as tmp:
        fake = FakeShitpost(({"value": 1}, [{"item": "a"}, "not-a-dict"]), tmp)

        with patch.object(fake, "_git_commit_push") as mock_commit:
            fake.run_tick()

        state = _read_jsonl(os.path.join(tmp, "state.jsonl"))
        assert len(state) == 1
        assert "error" in state[0]
        assert "non-dict item" in state[0]["error"]
        mock_commit.assert_not_called()


def test_run_tick_harness_timestamp_wins_over_plugin_timestamp():
    with tempfile.TemporaryDirectory() as tmp:
        fake = FakeShitpost({"value": 42, "timestamp": "0001-01-01T00:00:00+00:00"}, tmp)

        with patch.object(fake, "_git_commit_push") as mock_commit:
            fake.run_tick()

        state = _read_jsonl(os.path.join(tmp, "state.jsonl"))
        assert len(state) == 1
        assert state[0]["value"] == 42
        assert state[0]["timestamp"] != "0001-01-01T00:00:00+00:00"
        assert state[0]["timestamp"].endswith("+00:00")
        mock_commit.assert_called_once()


def test_run_tick_skips_when_another_tick_is_in_progress():
    with tempfile.TemporaryDirectory() as tmp:
        fake = FakeShitpost({"value": 42}, tmp)
        lock_path = os.path.join(tmp, ".tick.lock")

        # Hold the tick lock from outside.
        fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            with patch.object(fake, "_git_commit_push") as mock_commit:
                fake.run_tick()

            assert not os.path.exists(os.path.join(tmp, "state.jsonl"))
            assert not os.path.exists(os.path.join(tmp, "summary.json"))
            mock_commit.assert_not_called()
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
