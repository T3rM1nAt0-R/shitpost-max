"""Base class for every shitpost-max plugin.

A plugin only needs to subclass :class:`Shitpost`, set the three class
attributes, and implement :meth:`produce`. The harness handles state
persistence, summary snapshots, and commits uniformly. Pushing is handled
separately by :func:`git_push`, run periodically by the scheduler rather
than once per plugin tick - see that function's docstring for why.
"""

import contextlib
import fcntl
import json
import os
import subprocess
import sys
import time
import traceback
from abc import ABC, abstractmethod
from datetime import datetime, timezone

# Several plugins (pi-spigot, golden-ratio, sqrt2-stream, e-stream,
# digits-of-tau) are unbounded-integer digit spigots whose persisted state
# includes big ints that grow with every tick. Python 3.11+ refuses to
# str()/json-serialize an int over 4300 digits by default (the
# CVE-2020-10735 guard against attacker-supplied huge-int DoS) -- but these
# ints are our own algorithm's internal state, not untrusted input, and
# will only ever grow larger the longer any of these plugins keep running.
# pi-spigot hit this wall in production on 2026-07-14 after 860 ticks: every
# tick since has thrown ValueError inside json.dump and silently failed to
# save (caught by run_tick's per-plugin exception isolation, so it looked
# like the plugin had simply stopped rather than erroring). Disable the
# limit repo-wide, once, here -- every plugin imports this module.
sys.set_int_max_str_digits(0)

# Every plugin lives as a sibling directory in the same shared repo, so
# git operations (add/commit/push) touch one shared .git regardless of
# which plugin is ticking. The per-plugin .tick.lock below only prevents
# a single plugin from double-ticking itself - it does nothing to stop
# two *different* plugins from racing on git at the same moment, which
# will happen routinely once several plugins share a cadence. This lock
# is acquired repo-wide, only around the git step, so concurrent ticks
# queue instead of corrupting .git/index.lock or interleaving commits.
_GIT_LOCK_TIMEOUT_SECONDS = 30


def summarize_big_int(value: int, digit_threshold: int = 500) -> int | dict:
    """Return ``value`` as-is while it's small, else a bounded summary dict.

    Several plugins compute a number that grows exponentially forever
    (Catalan numbers, Fibonacci, Mersenne-derived perfect numbers, Pascal's
    triangle rows) and log the full value into state.jsonl -- and the git
    commit message -- every single tick, unbounded, forever. Left
    unchecked, that's exactly what grew pascal-row/state.jsonl to 164MB and
    silently broke every push since GitHub's 100MB per-file limit was
    crossed (~1142 ticks in, discovered 2026-07-16). Call this on any such
    value before returning it from produce(); it has no effect on whatever
    full-precision archive file the plugin keeps locally (untracked) --
    this only bounds what git is asked to store forever per tick.
    """
    text = str(value)
    if len(text) <= digit_threshold:
        return value
    return {
        "digit_count": len(text),
        "first_10": text[:10],
        "last_10": text[-10:],
        "truncated": True,
    }


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
        """Run one tick: produce, persist, and commit locally.

        Pushing happens separately - see :func:`git_push`, run periodically
        by the scheduler rather than once per tick.

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
                self._git_commit(message)
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

    def _persisted_state_path(self) -> str:
        """Path to this plugin's own small config/counter file.

        Distinct from state.jsonl/summary.json (the harness's own automatic
        per-tick log, written by _append_state/_write_summary above) - this
        is for whatever a plugin needs to remember between ticks to compute
        the *next* one (a counter, a running total, a "last seen" value).
        """
        return os.path.join(self._plugin_dir(), f"{self.name.replace('-', '_')}_state.json")

    def _load_persisted_state(self, default: dict) -> dict:
        """Load this plugin's own persisted state, or return ``default``.

        Added 2026-07-13: every plugin built so far reimplemented this exact
        load/save/corruption-handling pattern by hand (with real variation in
        correctness - missing imports, forgetting the atomic tmp-file write,
        wrong required-keys checks). One shared, tested implementation here
        removes an entire recurring bug class instead of relying on each
        generated file getting ~30 lines of boilerplate right independently.
        """
        path = self._persisted_state_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: {self.name} persisted state file is corrupt ({exc}); "
                    "starting fresh",
                    file=sys.stderr,
                )
                return dict(default)
            if not default.keys() <= state.keys():
                print(
                    f"warning: {self.name} persisted state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return dict(default)
            return state
        return dict(default)

    def _save_persisted_state(self, state: dict) -> None:
        path = self._persisted_state_path()
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _git_commit(self, message: str) -> None:
        """Commit ``state.jsonl`` and ``summary.json`` - local only, no push.

        Runs ``git add`` and ``git commit -m <message>`` in the plugin's own
        directory, holding a repo-wide lock for the duration so a
        concurrently-ticking sibling plugin can't race on the same shared
        ``.git``. Raises if the lock can't be acquired within
        ``_GIT_LOCK_TIMEOUT_SECONDS`` (surfaces as an error line via
        run_tick's existing exception handling, not a silent skip) or if
        any git command fails.

        Deliberately does not push (see ``git_push`` at module level): a
        local commit is a few milliseconds, but a push is a network round
        trip, and holding this same lock for both would mean every plugin
        serializes on network latency - the exact bottleneck that makes
        one-push-per-tick fall over well before 100 plugins. The scheduler
        runs ``git_push`` as its own periodic job instead, batching
        whatever's been committed locally since the last push into one
        network round trip.
        """
        plugin_dir = self._plugin_dir()
        with _repo_git_lock(self._repo_git_lock_path()):
            subprocess.run(
                # -f: .gitignore blanket-ignores **/state.jsonl and
                # **/summary.json (added 2026-07-13) so these two specific,
                # deliberately-tracked files aren't accidentally caught by
                # that same blanket rule for a brand-new plugin whose state
                # files have never been committed before -- git doesn't
                # retroactively apply .gitignore to already-tracked files,
                # which is why this only ever showed up for a plugin's very
                # first tick (caught 2026-07-14 registering 93 new plugins
                # in the scheduler for the first time; the 6 pre-existing
                # ones never hit this because their state files predated
                # the gitignore rule).
                ["git", "add", "-f", "state.jsonl", "summary.json"],
                cwd=plugin_dir,
                check=True,
            )
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=plugin_dir,
                check=True,
            )


@contextlib.contextmanager
def _repo_git_lock(lock_path: str):
    """Hold the shared repo-wide git lock for the duration of the block.

    Shared by :meth:`Shitpost._git_commit` and :func:`git_push` so a local
    commit and a push (or two pushes) never run concurrently and step on
    each other's ``.git`` state, while still letting commits (fast, local)
    and pushes (slower, network) each hold the lock only as long as they
    individually need it rather than one operation blocking on the other's
    typical duration.
    """
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
                        f"concurrent commit or push)"
                    )
                time.sleep(0.5)
        yield
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


def git_push(repo_root: str) -> None:
    """Push whatever's been locally committed since the last push.

    Meant to be run periodically (by the scheduler, as its own job on its
    own cadence) rather than once per plugin tick. This is the actual fix
    for the scaling ceiling one-push-per-tick hits: pushing is a network
    round trip (hundreds of ms to a couple seconds), and serializing every
    plugin's tick through that round trip caps out well before 100
    plugins sharing a cadence. Local commits (see ``Shitpost._git_commit``)
    are cheap and don't have this problem - only the push itself needs to
    be batched.

    If there's nothing new to push, ``git push`` exits quickly on its own
    ("Everything up-to-date") - this function doesn't try to detect that
    case itself, just always attempts the push under the shared lock.
    """
    lock_path = os.path.join(repo_root, ".git-push.lock")
    with _repo_git_lock(lock_path):
        subprocess.run(["git", "push"], cwd=repo_root, check=True)
