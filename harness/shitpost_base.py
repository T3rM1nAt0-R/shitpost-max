"""Base class for every shitpost-max plugin.

A plugin only needs to subclass :class:`Shitpost`, set the three class
attributes, and implement :meth:`produce`. The harness handles state
persistence, summary snapshots, commits, and pushes uniformly.
"""

import fcntl
import json
import os
import subprocess
import sys
import time
import traceback
from abc import ABC, abstractmethod
from datetime import datetime, timezone

# Every plugin lives as a sibling directory in the same shared repo, so
# git operations (add/commit/push) touch one shared .git regardless of
# which plugin is ticking. The per-plugin .tick.lock below only prevents
# a single plugin from double-ticking itself - it does nothing to stop
# two *different* plugins from racing on git at the same moment, which
# will happen routinely once several plugins share a cadence. This lock
# is acquired repo-wide, only around the git step, so concurrent ticks
# queue instead of corrupting .git/index.lock or interleaving commits.
_GIT_LOCK_TIMEOUT_SECONDS = 30


class Shitpost(ABC):
    """Abstract base for a shitpost-max plugin.

    Attributes:
        name: Directory name for this plugin.
        internal: Whether this plugin is hidden from the public dashboard.
            Must be set explicitly by every subclass.
        commit_template: ``str.format()`` template used for the git commit
            message. It is formatted with ``produce()``'s return dict, or
            with the summary dict for multi-line ticks.
    """

    name: str
    internal: bool
    commit_template: str

    @abstractmethod
    def produce(self) -> dict | tuple[dict, list[dict]] | None:
        """Return this tick's output.

        Three return shapes are supported:

        - ``dict``: one ``state.jsonl`` line; ``commit_template`` is
          formatted against it directly.
        - ``(summary_dict, [detail_dict, ...])``: each detail dict becomes
          its own ``state.jsonl`` line (all sharing the same tick
          timestamp); ``summary.json`` is written from ``summary_dict``;
          ``commit_template`` formats against ``summary_dict``.
        - ``None``: skip this tick entirely -- no state line, no summary,
          no commit.
        """
        raise NotImplementedError

    def run_tick(self) -> None:
        """Run one tick: produce, persist, commit, and push.

        Exceptions raised by :meth:`produce` are isolated: they are logged
        to stderr, recorded as an error line in ``state.jsonl``, and do
        not prevent this method from returning normally.

        A file lock (``.tick.lock`` in the plugin directory) prevents
        overlapping ticks from interleaving writes. If another tick is
        already running, this method logs and returns immediately.
        """
        plugin_dir = self._plugin_dir()
        lock_path = os.path.join(plugin_dir, ".tick.lock")
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
        try:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except (BlockingIOError, OSError):
                self._log_error("tick already in progress, skipping")
                return

            try:
                result = self.produce()
            except Exception:
                self._append_error(traceback.format_exc())
                return

            if result is None:
                return

            if isinstance(result, tuple):
                if len(result) != 2:
                    self._append_error(
                        f"produce() returned tuple of length {len(result)}, "
                        f"expected 2"
                    )
                    return
                summary, details = result
                if not isinstance(details, list):
                    self._append_error(
                        f"produce() returned tuple with second element of type "
                        f"{type(details).__name__}, expected list"
                    )
                    return
                if not all(isinstance(d, dict) for d in details):
                    self._append_error(
                        "produce() returned tuple with non-dict item in details list"
                    )
                    return
                timestamp = self._now_iso()
                for detail in details:
                    self._append_state(detail, timestamp=timestamp)
                self._write_summary(summary)
                commit_payload = summary
            elif isinstance(result, dict):
                self._append_state(result)
                self._write_summary(result)
                commit_payload = result
            else:
                self._append_error(
                    f"produce() returned unsupported type {type(result).__name__}"
                )
                return

            try:
                message = self.commit_template.format(**commit_payload)
            except Exception:
                self._append_error(traceback.format_exc())
                return

            try:
                self._git_commit_push(message)
            except Exception:
                self._log_error(traceback.format_exc())
                return
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            os.close(lock_fd)
            try:
                os.remove(lock_path)
            except OSError:
                pass

    def _plugin_dir(self) -> str:
        """Return the directory containing the plugin module."""
        module = sys.modules[self.__class__.__module__]
        return os.path.dirname(os.path.abspath(module.__file__))

    def _repo_git_lock_path(self) -> str:
        """Return the repo-root lock path shared by every plugin.

        Every plugin directory is a direct child of the same repo root
        (mirroring how ``harness/`` sits alongside every plugin), so the
        parent of ``_plugin_dir()`` is the repo root regardless of which
        plugin is asking.
        """
        repo_root = os.path.dirname(self._plugin_dir())
        return os.path.join(repo_root, ".git-push.lock")

    def _state_path(self) -> str:
        return os.path.join(self._plugin_dir(), "state.jsonl")

    def _summary_path(self) -> str:
        return os.path.join(self._plugin_dir(), "summary.json")

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _append_state(self, data: dict, *, timestamp: str | None = None) -> None:
        if timestamp is None:
            timestamp = self._now_iso()
        # Harness timestamp is written *after* the spread so it always wins
        # over any 'timestamp' key a plugin may have produced.
        line = {**data, "timestamp": timestamp}
        with open(self._state_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(line, separators=(",", ":"), sort_keys=True) + "\n")

    def _append_error(self, error_text: str) -> None:
        line = {"timestamp": self._now_iso(), "error": error_text}
        with open(self._state_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(line, separators=(",", ":"), sort_keys=True) + "\n")
        self._log_error(error_text)

    def _log_error(self, error_text: str) -> None:
        print(error_text, file=sys.stderr)

    def _write_summary(self, data: dict) -> None:
        with open(self._summary_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")

    def _git_commit_push(self, message: str) -> None:
        """Commit ``state.jsonl`` and ``summary.json`` and push.

        Runs ``git add``, ``git commit -m <message>``, and ``git push`` in
        the plugin's own directory, holding a repo-wide lock for the
        duration so a concurrently-ticking sibling plugin can't race on
        the same shared ``.git``. Raises if the lock can't be acquired
        within ``_GIT_LOCK_TIMEOUT_SECONDS`` (surfaces as an error line
        via run_tick's existing exception handling, not a silent skip) or
        if any git command fails.
        """
        plugin_dir = self._plugin_dir()
        lock_path = self._repo_git_lock_path()
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
        try:
            deadline = time.monotonic() + _GIT_LOCK_TIMEOUT_SECONDS
            while True:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except (BlockingIOError, OSError):
                    if time.monotonic() >= deadline:
                        raise TimeoutError(
                            f"could not acquire repo git lock within "
                            f"{_GIT_LOCK_TIMEOUT_SECONDS}s (held by a "
                            f"concurrently-ticking plugin)"
                        )
                    time.sleep(0.5)

            subprocess.run(
                ["git", "add", "state.jsonl", "summary.json"],
                cwd=plugin_dir,
                check=True,
            )
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=plugin_dir,
                check=True,
            )
            subprocess.run(
                ["git", "push"],
                cwd=plugin_dir,
                check=True,
            )
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            os.close(lock_fd)
