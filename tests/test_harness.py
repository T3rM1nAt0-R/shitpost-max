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

        with patch.object(fake, "_git_commit") as mock_commit:
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

        with patch.object(fake, "_git_commit") as mock_commit:
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

        with patch.object(broken, "_git_commit") as mock_commit:
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

        with patch.object(fake, "_git_commit") as mock_commit:
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
def test_run_tick_git_commit_integration():
    """A real git repo commits successfully - and does NOT attempt a push
    (no remote configured at all here; if run_tick tried to push, this
    would raise, since _git_commit no longer pushes)."""
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
        fake.run_tick()

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


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_git_push_pushes_local_commits_to_remote():
    """git_push actually pushes what's been locally committed - proven with
    a real local 'remote' (a bare repo), not just checking it doesn't raise."""
    from harness.shitpost_base import git_push

    with tempfile.TemporaryDirectory() as remote_dir, tempfile.TemporaryDirectory() as work_dir:
        subprocess.run(["git", "init", "--bare"], cwd=remote_dir, check=True, capture_output=True)
        subprocess.run(["git", "init"], cwd=work_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "--local", "user.name", "Test User"],
            cwd=work_dir, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "--local", "user.email", "test@example.com"],
            cwd=work_dir, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "remote", "add", "origin", remote_dir],
            cwd=work_dir, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "checkout", "-b", "main"], cwd=work_dir, check=True, capture_output=True,
        )

        with open(os.path.join(work_dir, "file.txt"), "w", encoding="utf-8") as f:
            f.write("content")
        subprocess.run(["git", "add", "file.txt"], cwd=work_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "local commit"], cwd=work_dir, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "push", "-u", "origin", "main"], cwd=work_dir, check=True, capture_output=True,
        )

        # A second local commit, not yet on the remote.
        with open(os.path.join(work_dir, "file2.txt"), "w", encoding="utf-8") as f:
            f.write("more content")
        subprocess.run(["git", "add", "file2.txt"], cwd=work_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "second commit"], cwd=work_dir, check=True, capture_output=True,
        )

        remote_log_before = subprocess.run(
            ["git", "log", "--oneline", "main"], cwd=remote_dir, check=True,
            capture_output=True, text=True,
        )
        assert "second commit" not in remote_log_before.stdout

        git_push(work_dir)

        remote_log_after = subprocess.run(
            ["git", "log", "--oneline", "main"], cwd=remote_dir, check=True,
            capture_output=True, text=True,
        )
        assert "second commit" in remote_log_after.stdout


def test_run_tick_commit_template_key_error_is_isolated():
    """A bad commit_template referencing a missing key must not crash the tick."""
    with tempfile.TemporaryDirectory() as tmp:
        fake = FakeShitpost({"value": 42}, tmp)
        fake.commit_template = "tick: {missing}"

        with patch.object(fake, "_git_commit") as mock_commit:
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

        with patch.object(fake, "_git_commit") as mock_commit:
            fake.run_tick()

        state = _read_jsonl(os.path.join(tmp, "state.jsonl"))
        assert len(state) == 1
        assert "error" in state[0]
        assert "tuple of length 3" in state[0]["error"]
        mock_commit.assert_not_called()


def test_run_tick_details_non_dict_is_isolated():
    with tempfile.TemporaryDirectory() as tmp:
        fake = FakeShitpost(({"value": 1}, [{"item": "a"}, "not-a-dict"]), tmp)

        with patch.object(fake, "_git_commit") as mock_commit:
            fake.run_tick()

        state = _read_jsonl(os.path.join(tmp, "state.jsonl"))
        assert len(state) == 1
        assert "error" in state[0]
        assert "non-dict item" in state[0]["error"]
        mock_commit.assert_not_called()


def test_run_tick_harness_timestamp_wins_over_plugin_timestamp():
    with tempfile.TemporaryDirectory() as tmp:
        fake = FakeShitpost({"value": 42, "timestamp": "0001-01-01T00:00:00+00:00"}, tmp)

        with patch.object(fake, "_git_commit") as mock_commit:
            fake.run_tick()

        state = _read_jsonl(os.path.join(tmp, "state.jsonl"))
        assert len(state) == 1
        assert state[0]["value"] == 42
        assert state[0]["timestamp"] != "0001-01-01T00:00:00+00:00"
        assert state[0]["timestamp"].endswith("+00:00")
        mock_commit.assert_called_once()


def test_git_commit_serializes_across_sibling_plugins():
    """Two sibling plugins ticking at once must not race on the shared repo lock -
    one blocks until the other releases, rather than corrupting .git concurrently."""
    import threading
    import time

    with tempfile.TemporaryDirectory() as repo_root:
        plugin_a_dir = os.path.join(repo_root, "plugin-a")
        plugin_b_dir = os.path.join(repo_root, "plugin-b")
        os.makedirs(plugin_a_dir)
        os.makedirs(plugin_b_dir)

        plugin_a = FakeShitpost({"value": 1}, plugin_a_dir)
        plugin_b = FakeShitpost({"value": 2}, plugin_b_dir)

        events = []
        events_lock = threading.Lock()

        with patch.object(
            plugin_a,
            "_git_commit",
            wraps=lambda msg: _locked_call(plugin_a, "a", 0.2, events, events_lock),
        ), patch.object(
            plugin_b,
            "_git_commit",
            wraps=lambda msg: _locked_call(plugin_b, "b", 0.2, events, events_lock),
        ):
            t_a = threading.Thread(target=plugin_a.run_tick)
            t_b = threading.Thread(target=plugin_b.run_tick)
            t_a.start()
            time.sleep(0.05)  # ensure a acquires the lock first
            t_b.start()
            t_a.join()
            t_b.join()

        # b must not start until a has fully finished - proves serialization,
        # not just "both eventually ran".
        assert events == ["a-start", "a-end", "b-start", "b-end"]


def _locked_call(plugin, label, sleep_seconds, events, events_lock):
    """Exercise the real repo lock via the plugin's actual lock path, then
    simulate a slow git operation so overlap would be observable if the lock
    didn't serialize."""
    import fcntl
    import time

    lock_path = plugin._repo_git_lock_path()
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
    fcntl.flock(fd, fcntl.LOCK_EX)
    try:
        with events_lock:
            events.append(f"{label}-start")
        time.sleep(sleep_seconds)
        with events_lock:
            events.append(f"{label}-end")
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def test_git_commit_raises_on_lock_timeout():
    """If the repo lock is held past the timeout, the tick must surface an
    error rather than hang forever or silently skip the commit."""
    import fcntl

    with tempfile.TemporaryDirectory() as repo_root:
        plugin_dir = os.path.join(repo_root, "plugin-a")
        os.makedirs(plugin_dir)
        fake = FakeShitpost({"value": 1}, plugin_dir)

        lock_path = fake._repo_git_lock_path()
        holder_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
        fcntl.flock(holder_fd, fcntl.LOCK_EX)
        try:
            with patch(
                "harness.shitpost_base._GIT_LOCK_TIMEOUT_SECONDS", 0.3
            ):
                with pytest.raises(TimeoutError):
                    fake._git_commit("tick: 1")
        finally:
            fcntl.flock(holder_fd, fcntl.LOCK_UN)
            os.close(holder_fd)


def test_run_tick_skips_when_another_tick_is_in_progress():
    with tempfile.TemporaryDirectory() as tmp:
        fake = FakeShitpost({"value": 42}, tmp)
        lock_path = os.path.join(tmp, ".tick.lock")

        # Hold the tick lock from outside.
        fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            with patch.object(fake, "_git_commit") as mock_commit:
                fake.run_tick()

            assert not os.path.exists(os.path.join(tmp, "state.jsonl"))
            assert not os.path.exists(os.path.join(tmp, "summary.json"))
            mock_commit.assert_not_called()
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
