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

2026-07-14: plugin ticks are dispatched to a bounded thread pool
(``_TICK_EXECUTOR``) instead of running inline inside ``step()``. Before
this, the whole scheduler was single-threaded and strictly sequential - one
slow plugin (real network calls, real local LLM inference taking minutes)
blocked every other plugin's on-time tick behind it. This was invisible at
6 plugins but became a real, observed problem registering the other 93:
every job starts "due now" on a cold start, so the first pass ran through
~99 jobs in alphabetical order, and a handful of genuinely slow ones
(temperature-lab's real LLM inference alone can take 4+ minutes) delayed
everything alphabetically after them by that much. Running ticks
concurrently is safe: ``Shitpost._git_commit`` and ``git_push`` already
share one repo-wide lock (``.git-push.lock``) for the git operations
themselves, so concurrent ticks only ever serialize on the actual
add+commit (milliseconds), while each tick's real work (subprocess spawn,
network I/O, LLM inference) genuinely runs in parallel. The push job itself
stays inline in the main loop, not offloaded - it's already fast
(network round trip, not the bottleneck) and this way it's never starved
behind a queue of slow tick threads.
"""
import concurrent.futures
import heapq
import os
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

# 2026-07-17: added the 90 plugins built across this session's local-build-loop
# marathon (the remaining bounded ideas from the 93-idea backlog, minus 2
# deliberately-skipped unbounded ideas and 1 never actually built). Cadence
# for each comes directly from its own design.md's "## Cadence" line -- 60s
# default for pure-computation plugins, 200-300s for fixed-list-cycling
# plugins with slightly heavier per-tick work, 600-1800s for anything that
# calls a real external API (rate-limit-conscious), and 900-3600s for
# anything doing real local LLM inference (a single produce() call can take
# tens of seconds) or sharing a rate-limited NASA/DEMO_KEY budget.
PLUGINS += [
    ("acronym-expander", 120),
    ("api-snapshot-diff", 250),
    ("asteroid-watch", 3600),
    ("aurora-forecast", 1200),
    ("babylonian-sqrt", 60),
    ("binary-heap-demo", 50),
    ("birthday-paradox", 40),
    ("bitcoin-fees", 600),
    ("branch-age-tracker", 250),
    ("changelog-gen", 250),
    ("clickbait-factory", 110),
    ("code-complexity-watch", 250),
    ("config-validator", 250),
    ("continued-fraction", 60),
    ("conway-life", 60),
    ("corporate-bs-generator", 70),
    ("count-min-sketch", 60),
    ("covid-wastewater", 1800),
    ("cowclick-generator", 140),
    ("credit-card-sim", 180),
    ("dependency-watch", 250),
    ("dividend-tracker", 200),
    ("dockerfile-linter", 250),
    ("egyptian-fraction", 60),
    ("emi-calculator", 200),
    ("env-diff", 250),
    ("epidemic-sim", 60),
    ("euphemism-engine", 85),
    ("extraction-bench", 900),
    ("fd-calculator", 200),
    ("fermat-factor", 60),
    ("few-shot-drift", 900),
    ("forest-fire-sim", 35),
    ("fortune-cookie-factory", 130),
    ("genetic-hello", 10),
    ("git-blame-stats", 250),
    ("gold-silver-ratio", 900),
    ("haiku-stream", 300),
    ("happy-numbers", 60),
    ("horoscope-gen", 150),
    ("hyperloglog-estimator", 30),
    ("inflation-calculator", 200),
    ("iterated-prisoner", 25),
    ("kdtree-builder", 80),
    ("knuth-morris-pratt", 60),
    ("langton-ant", 20),
    ("levenshtein-watch", 60),
    ("llm-self-eval", 900),
    ("llm-vs-template", 900),
    ("loan-amortization", 180),
    ("logprobs-tracker", 1200),
    ("lorem-ipsum-stream", 15),
    ("lumpsum-calculator", 200),
    ("makefile-help", 250),
    ("mars-weather", 3600),
    ("mempool-watch", 600),
    ("minhash-sig", 100),
    ("mobius-function", 60),
    ("monty-hall-sim", 30),
    ("moon-phase", 3600),
    ("multi-armed-bandit", 30),
    ("multiplicative-persistence", 60),
    ("pirate-translator", 95),
    ("portmanteau-gen", 100),
    ("prompt-chaining-lab", 900),
    ("prompt-template-lab", 900),
    ("radix-sort-tick", 40),
    ("random-walk-2d", 60),
    ("response-length-lab", 900),
    ("retirement-sim", 180),
    ("rhyme-time", 90),
    ("schelling-segregation", 50),
    ("sentiment-drift", 900),
    ("sierpinski-chaos", 15),
    ("sieving-sundaram", 60),
    ("simhash-near-dup", 75),
    ("sip-simulator", 180),
    ("stackoverflow-tags", 1800),
    ("stern-brocot", 90),
    ("stock-index-ticker", 900),
    ("system-prompt-tester", 900),
    ("tax-bracket-viewer", 200),
    ("test-splitter", 250),
    ("timsort-metrics", 45),
    ("todo-scanner", 250),
    ("token-counter-demo", 300),
    ("top-pypi-packages", 3600),
    ("treasury-yield", 1800),
    ("trie-stats", 60),
    ("zero-shot-bench", 900),
]

# 2026-07-17: the 3 backlog ideas that were skipped/missed in the marathon
# above -- aliquot-sequences and look-and-say were originally flagged
# "unbounded" (open-ended growth risk) and made safely bounded via a hard
# step/term cap + reset (see each plugin's own proposal.md for the exact
# reasoning); cuckoo-filter was marked bounded but simply never got built.
PLUGINS += [
    ("aliquot-sequences", 90),
    ("look-and-say", 60),
    ("cuckoo-filter", 90),
]

# How often the pusher runs, independent of any plugin's own cadence.
PUSH_CADENCE_SECONDS = 20


# Hard ceiling on how long any single plugin's tick.py may run. This is
# the shared thread pool's only defense against a plugin whose own logic
# hangs (an infinite retry loop, a stuck network call) rather than crashing:
# each of the pool's workers blocks on subprocess.run() until the child
# exits, so one hung tick can quietly occupy a worker forever, and once
# enough of them pile up (silicon-valley-buzzword-bot did exactly this on
# 2026-07-14 -- its buzzword-uniqueness loop could never terminate once its
# small fixed vocabulary was exhausted) the *entire* pool is starved and no
# other plugin ticks at all, even though each one's own per-plugin flock
# only prevents that one plugin's ticks from overlapping. 120s is far above
# every plugin's real cadence-appropriate runtime (the slowest legitimate
# work, real local LLM inference, is documented above as ~4 minutes at the
# high end for a couple of plugins -- generous headroom is intentional; the
# goal is only to bound a genuine hang, not to race normal ticks).
TICK_TIMEOUT_SECONDS = 300


def run_tick_subprocess(
    plugin_dir: str, repo_root: Path = REPO_ROOT, timeout: float = TICK_TIMEOUT_SECONDS
) -> None:
    """Run one plugin's tick.py as a subprocess, exactly like cron would."""
    try:
        result = subprocess.run(
            [sys.executable, "tick.py"],
            cwd=repo_root / plugin_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            print(
                f"[{plugin_dir}] tick.py exited {result.returncode}: {result.stderr}",
                file=sys.stderr,
            )
    except subprocess.TimeoutExpired:
        print(
            f"[{plugin_dir}] tick.py timed out after {timeout}s, killed",
            file=sys.stderr,
        )
    except Exception as exc:
        # Runs inside a thread pool worker (see _TICK_EXECUTOR) - an
        # exception here would otherwise be silently swallowed by
        # concurrent.futures unless something calls .result() on the
        # future, which nothing does (fire-and-forget by design).
        print(f"[{plugin_dir}] unhandled exception dispatching tick: {exc}", file=sys.stderr)


# Bounded worker pool plugin ticks are dispatched to, so a burst of
# simultaneously-due jobs (every job starts "due now" on a cold start) runs
# concurrently instead of piling up behind a single sequential loop. Kept
# modest by default - this is spawning real subprocesses (each with its own
# interpreter startup cost) and some plugins do real local LLM inference,
# which is itself CPU/GPU-bound on the same host running this scheduler, so
# unbounded concurrency would just trade "slow scheduler" for "slow
# everything else on the box." Override via SCHEDULER_MAX_WORKERS if needed.
_TICK_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=int(os.environ.get("SCHEDULER_MAX_WORKERS", "8")),
    thread_name_prefix="tick",
)


def submit_tick(plugin_dir: str) -> None:
    """Dispatch one plugin's tick to the background thread pool and return
    immediately, instead of blocking the scheduler's main loop until it
    finishes. Safe even if the same plugin's previous tick is still
    running when this one is submitted: Shitpost.run_tick's own
    ``.tick.lock`` (non-blocking flock) makes the second invocation log
    "tick already in progress, skipping" and return immediately, rather
    than racing on the same plugin's own state files."""
    _TICK_EXECUTOR.submit(run_tick_subprocess, plugin_dir)


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
        (plugin_dir, cadence, lambda p=plugin_dir: submit_tick(p))
        for plugin_dir, cadence in PLUGINS
    ]
    # push is NOT offloaded to _TICK_EXECUTOR - stays inline in the main
    # scheduler loop (see module docstring for why).
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
