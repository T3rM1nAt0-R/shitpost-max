#!/usr/bin/env python3
"""Single-process scheduler for every plugin's tick, replacing one cron line
per plugin.

The core idea is a min-heap ("sorted pile, soonest on top") of
``(next_due_time, plugin_dir, cadence_seconds)``. The scheduler always pops
whichever plugin is due soonest, waits until it's actually due, runs it,
then pushes it back with its *next* due time. Popping/pushing a Python
heap is O(log n), so this comfortably handles far more than the handful
of plugins registered today.

Each tick still runs as its own subprocess (``python3 tick.py``, exactly
what cron would have invoked) rather than importing every plugin's module
into this one process. That's a deliberate choice, not an oversight: two
unrelated plugins could someday pick the same module name (e.g. two
different plugins both naming their main file ``plugin.py``), and Python's
import cache is keyed by module name process-wide - importing everything
into one process would make that a real, silent collision risk as the
plugin count grows. A subprocess per tick costs a bit of process-spawn
overhead but keeps every plugin's namespace fully isolated, matching how
they already run under cron today.
"""
import heapq
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# (plugin directory name, cadence in seconds). Cadence per each plugin's own
# design.md; base-converter doesn't state one, so it uses the majority
# default (60s) like the others.
PLUGINS = [
    ("pi-spigot", 60),
    ("uptime-witness", 60),
    ("golden-ratio", 60),
    ("fibonacci-full", 60),
    ("base-converter", 60),
    ("commit-poet", 600),
]


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


class Scheduler:
    """Min-heap scheduler over a set of (plugin_dir, cadence_seconds) pairs.

    ``run_tick``, ``clock``, and ``sleeper`` are injectable so ``step()`` can
    be unit-tested without real subprocesses or real waiting.
    """

    def __init__(self, plugins, run_tick=run_tick_subprocess, clock=time.monotonic, sleeper=time.sleep):
        self._run_tick = run_tick
        self._clock = clock
        self._sleep = sleeper
        now = clock()
        # Every plugin starts "due now" so the first pass through fires
        # each one once immediately, then settles into its real cadence.
        self._heap = [(now, plugin_dir, cadence) for plugin_dir, cadence in plugins]
        heapq.heapify(self._heap)

    def step(self) -> str:
        """Run exactly one tick: pop the soonest-due plugin, wait if it isn't
        due yet, run it, and reschedule it. Returns the plugin_dir that ran,
        so callers/tests can observe ordering."""
        due_time, plugin_dir, cadence = heapq.heappop(self._heap)

        sleep_for = due_time - self._clock()
        if sleep_for > 0:
            self._sleep(sleep_for)

        self._run_tick(plugin_dir)

        # Reschedule from the *original* due time, not "now" - if a tick
        # runs a little late, the next one is still due on the original
        # cadence instead of drifting later and later.
        heapq.heappush(self._heap, (due_time + cadence, plugin_dir, cadence))

        return plugin_dir

    def run_forever(self) -> None:
        while True:
            self.step()


def main() -> None:
    scheduler = Scheduler(PLUGINS)
    print(f"Scheduler started with {len(PLUGINS)} plugins: {[p for p, _ in PLUGINS]}")
    scheduler.run_forever()


if __name__ == "__main__":
    main()
