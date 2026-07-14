#!/usr/bin/env python3
"""Single-process scheduler for every plugin's tick, replacing one cron line
per plugin - plus a periodic push job that batches network pushes instead
of pushing once per tick.

The core idea is a min-heap ("sorted pile, soonest on top") of
``(next_due_time, job_name, cadence_seconds)``. The scheduler always pops
whichever job is due soonest, waits until it's actually due, runs it, then
pushes it back with its *next* due time. Popping/pushing a Python heap is
O(log n), so this comfortably handles far more than the handful of jobs
registered today.

Two kinds of job share the same heap:
- **Plugin ticks** run ``tick.py`` as a subprocess (exactly what cron would
  have invoked) rather than importing every plugin's module into this one
  process - two unrelated plugins could someday pick the same module name
  (e.g. two different "plugin.py"s), and Python's import cache is keyed by
  name process-wide. Subprocess-per-tick keeps every plugin's namespace
  isolated at the cost of some spawn overhead (acceptable at this scale).
  Each tick only commits locally (see ``Shitpost._git_commit``) - it does
  not push.
- **The pusher** runs ``git_push`` on its own cadence (independent of any
  plugin's), batching whatever's been locally committed since the last
  push into one network round trip. This is what actually lets the whole
  thing scale past a few dozen plugins - see ``git_push``'s docstring in
  ``shitpost_base.py`` for why per-tick pushing doesn't.
"""
import heapq
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Make the repo root importable so `harness.shitpost_base` resolves whether
# this is run as `python3 harness/scheduler.py` (systemd invokes it exactly
# this way - Python only auto-adds the script's own directory to sys.path,
# not its parent) or as `python3 -m harness.scheduler` from the repo root.
# Same pattern every plugin's tick.py already uses for the same reason.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from harness.shitpost_base import git_push  # noqa: E402

# (plugin directory name, cadence in seconds). Cadence per each plugin's own
# design.md; base-converter doesn't state one, so it uses the majority
# default (60s) like the others.
#
# 2026-07-14: added the other 93 plugins built across the local-build-loop
# marathon -- they were fully built, verified, and merged to main, but this
# list was never updated, so none of them had ever actually ticked in
# production (confirmed via the shitpost dashboard: 61/70 non-internal
# entries showed tick_count 0). Cadence for each: 60s default (matching the
# existing plugins), 600s for anything that calls a real external API,
# spawns a subprocess, or hits the docker socket -- to avoid hammering rate
# limits or, for the couple that do real local LLM inference
# (llm-vs-llm, temperature-lab, prompt-injection-lab), because a single
# produce() call can itself take minutes.
PLUGINS = [
    ("pi-spigot", 60),
    ("uptime-witness", 60),
    ("golden-ratio", 60),
    ("fibonacci-full", 60),
    ("base-converter", 60),
    ("commit-poet", 600),
    ("10x-engineer", 60),
    ("agile-theater", 60),
    ("anagram-hunter", 60),
    ("aqi-blr", 600),
    ("backup-witness", 600),
    ("balance-witness", 60),
    ("bloom-filter-demo", 60),
    ("card-shuffler", 60),
    ("catalan-numbers", 60),
    ("cert-watch", 600),
    ("certificate-mill", 60),
    ("collatz-explorer", 60),
    ("commit-batcher", 60),
    ("commit-driven-development", 60),
    ("compound-clock", 60),
    ("compression-lab", 60),
    ("container-of-the-day", 600),
    ("cron-vs-timer", 60),
    ("crypto-tick", 600),
    ("dice-fairness", 60),
    ("diff-engine", 60),
    ("digits-of-tau", 60),
    ("disk-canary", 600),
    ("docker-census", 600),
    ("domain-watch", 600),
    ("dungeon-of-the-day", 60),
    ("e-stream", 60),
    ("earthquake-log", 600),
    ("economy-sim-tick", 60),
    ("emoji-summary", 600),
    ("fake-changelog", 60),
    ("fear-greed-index", 600),
    ("gacha-oracle", 60),
    ("gas-prices", 600),
    ("git-hook-theater", 600),
    ("github-trending", 600),
    ("graph-of-the-day", 60),
    ("green-square-maxxer", 60),
    ("haiku-daily", 60),
    ("hallucination-witness", 60),
    ("hash-collision-hunt", 60),
    ("healthcheck-endpoint", 60),
    ("high-iq-certifier", 60),
    ("hn-frontpage", 600),
    ("iss-tracker", 600),
    ("json-mode-witness", 60),
    ("latency-log", 600),
    ("litellm-tokens", 600),
    ("llm-vs-llm", 600),
    ("log-rotator", 60),
    ("loot-table-fuzzer", 60),
    ("lru-cache-witness", 60),
    ("markov-nonsense", 60),
    ("maze-solver", 60),
    ("meta-tracker", 60),
    ("model-diff", 600),
    ("name-generator", 60),
    ("networth-witness", 60),
    ("npm-downloads", 600),
    ("palindrome-generator", 60),
    ("pascal-row", 60),
    ("perfect-numbers", 60),
    ("playtest-bot", 60),
    ("primes-forever", 60),
    ("prompt-injection-lab", 600),
    ("rag-decay", 600),
    ("ram-witness", 60),
    ("rate-limit-lab", 60),
    ("reddit-titles", 600),
    ("regex-of-the-day", 60),
    ("regression-canary", 600),
    ("retry-with-backoff", 600),
    ("rss-firehose", 600),
    ("rupee-cost-averaging-sim", 60),
    ("selfhealing-demo", 60),
    ("shitpost-max-meta", 60),
    ("silicon-valley-buzzword-bot", 60),
    ("sorting-race", 60),
    ("spotify-charts", 600),
    ("sqrt2-stream", 60),
    ("steam-playercount", 600),
    ("subscription-audit", 60),
    ("temp-log", 600),
    ("temperature-lab", 600),
    ("thought-leader", 60),
    ("token-golf", 60),
    ("translation-telephone", 60),
    ("tunnel-health", 600),
    ("twin-primes", 60),
    ("usd-inr", 600),
    ("weather-blr", 600),
    ("wikipedia-featured", 600),
    ("word-of-the-day", 600),
]

# How often the pusher runs, independent of any plugin's own cadence.
PUSH_CADENCE_SECONDS = 20


def run_tick_subprocess(plugin_dir: str, repo_root: Path = REPO_ROOT) -> None:
    """Run one plugin's tick.py as a subprocess, exactly like cron would."""
    result = subprocess.run(
        [sys.executable, "tick.py"],
        cwd=repo_root / plugin_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(
            f"[{plugin_dir}] tick.py exited {result.returncode}: {result.stderr}",
            file=sys.stderr,
        )


def push_job(repo_root: Path = REPO_ROOT) -> None:
    """Scheduler job wrapper around ``git_push`` - logs instead of crashing
    the whole scheduler if a push fails (e.g. transient network issue),
    matching each plugin tick's own error-isolation philosophy."""
    try:
        git_push(str(repo_root))
    except Exception as exc:
        print(f"[push] failed: {exc}", file=sys.stderr)


class Scheduler:
    """Min-heap scheduler over a set of named jobs, each with its own
    cadence and action callable.

    ``clock`` and ``sleeper`` are injectable so ``step()`` can be
    unit-tested without real waiting.
    """

    def __init__(self, jobs, clock=time.monotonic, sleeper=time.sleep):
        """``jobs``: iterable of ``(name, cadence_seconds, action)`` triples,
        where ``action`` is a zero-argument callable run when that job is
        due."""
        self._clock = clock
        self._sleep = sleeper
        self._actions = {name: action for name, _cadence, action in jobs}
        now = clock()
        # Every job starts "due now" so the first pass fires each one
        # immediately, then settles into its real cadence.
        self._heap = [(now, name, cadence) for name, cadence, _action in jobs]
        heapq.heapify(self._heap)

    def step(self) -> str:
        """Run exactly one job: pop the soonest-due one, wait if it isn't
        due yet, run it, and reschedule it. Returns the job name that ran,
        so callers/tests can observe ordering."""
        due_time, name, cadence = heapq.heappop(self._heap)

        sleep_for = due_time - self._clock()
        if sleep_for > 0:
            self._sleep(sleep_for)

        self._actions[name]()

        # Reschedule from the *original* due time, not "now" - if a job
        # runs a little late, the next one is still due on the original
        # cadence instead of drifting later and later.
        heapq.heappush(self._heap, (due_time + cadence, name, cadence))

        return name

    def run_forever(self) -> None:
        while True:
            self.step()


def default_jobs():
    jobs = [
        (plugin_dir, cadence, lambda p=plugin_dir: run_tick_subprocess(p))
        for plugin_dir, cadence in PLUGINS
    ]
    jobs.append(("push", PUSH_CADENCE_SECONDS, push_job))
    return jobs


def main() -> None:
    jobs = default_jobs()
    scheduler = Scheduler(jobs)
    print(f"Scheduler started with {len(jobs)} jobs: {[name for name, _, _ in jobs]}")

    # Import-check mode: confirms the module loaded and jobs were built
    # correctly (the exact thing that broke in production - see
    # test_scheduler_runs_standalone_exactly_as_systemd_invokes_it) without
    # actually running any tick or push. Every job starts "due now", so
    # calling run_forever() here would fire real ticks/pushes immediately.
    import os

    if os.environ.get("SCHEDULER_IMPORT_CHECK_ONLY"):
        print("Import check OK, exiting without running any job.")
        return

    scheduler.run_forever()


if __name__ == "__main__":
    main()
