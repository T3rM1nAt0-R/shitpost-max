import time

from harness.scheduler import Scheduler, submit_tick


class FakeClock:
    """A controllable clock: advances only when told to, never real time."""

    def __init__(self, start=0.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def make_scheduler(job_specs, clock, run_log):
    """``job_specs``: list of (name, cadence). Each job's action just
    records (time, name) to run_log - real actions (subprocess ticks,
    git_push) are exercised separately, not here."""

    def fake_sleep(seconds):
        # A real scheduler would block for `seconds`; the test just
        # advances the fake clock by the same amount instead of waiting.
        clock.advance(seconds)

    jobs = [
        (name, cadence, lambda n=name: run_log.append((clock.now, n)))
        for name, cadence in job_specs
    ]
    return Scheduler(jobs, clock=clock, sleeper=fake_sleep)


def test_step_runs_soonest_due_job_first():
    clock = FakeClock(start=100.0)
    run_log = []
    scheduler = make_scheduler(
        [("slow", 600), ("fast", 60)], clock=clock, run_log=run_log
    )

    # Both start "due now" - heap order among equal due-times falls back to
    # name string comparison, so this just confirms step() runs one of them
    # without erroring and returns its name.
    ran = scheduler.step()
    assert ran in ("slow", "fast")
    assert run_log == [(100.0, ran)]


def test_faster_cadence_job_runs_more_often():
    clock = FakeClock(start=0.0)
    run_log = []
    scheduler = make_scheduler(
        [("fast", 10), ("slow", 100)], clock=clock, run_log=run_log
    )

    for _ in range(15):
        scheduler.step()

    fast_runs = [t for t, name in run_log if name == "fast"]
    slow_runs = [t for t, name in run_log if name == "slow"]
    assert len(fast_runs) > len(slow_runs)
    # fast (cadence 10) should have run roughly 10x as often as slow (cadence 100).
    assert len(fast_runs) >= 9


def test_reschedule_uses_original_due_time_not_now_to_avoid_drift():
    clock = FakeClock(start=0.0)
    calls = []

    def slow_action():
        calls.append(clock.now)
        clock.advance(5.0)  # this job itself "takes" 5s

    scheduler = Scheduler(
        [("only", 60, slow_action)], clock=clock, sleeper=lambda s: clock.advance(s)
    )

    scheduler.step()  # runs at t=0, "takes" until t=5
    due_time, name, cadence = scheduler._heap[0]
    # Must be due_time(0) + cadence(60) = 60, not now(5) + cadence(60) = 65 -
    # otherwise a slow job would permanently push every future run later.
    assert due_time == 60


def test_jobs_never_collide_in_the_heap():
    """Sanity check that the heap always holds exactly one entry per job,
    regardless of how many steps run - nothing gets dropped or duplicated."""
    clock = FakeClock(start=0.0)
    run_log = []
    job_specs = [("a", 7), ("b", 13), ("c", 5), ("d", 30)]
    scheduler = make_scheduler(job_specs, clock=clock, run_log=run_log)

    for _ in range(50):
        scheduler.step()

    assert len(scheduler._heap) == len(job_specs)
    heap_names = {entry[1] for entry in scheduler._heap}
    assert heap_names == {name for name, _ in job_specs}


def test_push_job_runs_independently_of_plugin_cadences():
    """The pusher is just another job in the same heap - confirms it
    interleaves with plugin-tick jobs rather than needing special-casing."""
    clock = FakeClock(start=0.0)
    run_log = []
    scheduler = make_scheduler(
        [("pi-spigot", 60), ("push", 20)], clock=clock, run_log=run_log
    )

    for _ in range(10):
        scheduler.step()

    push_runs = [t for t, name in run_log if name == "push"]
    tick_runs = [t for t, name in run_log if name == "pi-spigot"]
    assert len(push_runs) > len(tick_runs)
    assert len(push_runs) >= 5


def test_default_jobs_includes_all_plugins_and_a_pusher():
    from harness.scheduler import default_jobs

    jobs = default_jobs()
    names = {name for name, _cadence, _action in jobs}
    assert "push" in names
    assert "pi-spigot" in names
    assert "commit-poet" in names


def test_scheduler_runs_standalone_exactly_as_systemd_invokes_it():
    """Regression test: `from harness.scheduler import Scheduler` works fine
    under pytest (repo root is already on sys.path via pytest's own
    mechanism), but that's NOT how this actually gets run in production -
    systemd invokes it as `python3 harness/scheduler.py` from the repo
    root, and Python only auto-adds the *script's own* directory to
    sys.path, not its parent. That gap broke the very first real
    deployment (ModuleNotFoundError: No module named 'harness') despite
    every other test passing. This runs the real file as a real
    subprocess, the same way systemd does, to catch that class of bug -
    using SCHEDULER_IMPORT_CHECK_ONLY so it exits right after a successful
    import instead of actually running any tick/push (every job starts
    "due now", so a real run would fire real subprocess ticks and pushes
    against the live repo during a test)."""
    import os
    import subprocess
    import sys

    from harness.scheduler import REPO_ROOT

    env = {**os.environ, "SCHEDULER_IMPORT_CHECK_ONLY": "1"}
    result = subprocess.run(
        [sys.executable, "harness/scheduler.py"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "Import check OK" in result.stdout
    assert "ModuleNotFoundError" not in result.stderr


def test_step_does_not_block_on_a_slow_action():
    """The whole point of offloading ticks to a thread pool (submit_tick):
    step() returning should not require the actual work to have finished.
    Regression test for the pre-2026-07-14 design, where a single slow
    plugin (real LLM inference, real network calls) blocked every other
    due job behind it in the same single-threaded loop."""
    clock = FakeClock(start=0.0)
    started = []
    finished = []
    release = []

    def slow_action():
        started.append(clock.now)
        # Block this thread (not the scheduler's) until the test lets go.
        while not release:
            time.sleep(0.01)
        finished.append(clock.now)

    import concurrent.futures

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    scheduler = Scheduler(
        [("slow", 60, lambda: executor.submit(slow_action))],
        clock=clock,
        sleeper=lambda s: clock.advance(s),
    )

    ran = scheduler.step()
    assert ran == "slow"
    # step() must have returned already, well before slow_action releases -
    # proving the scheduler's own loop isn't the thing blocked.
    deadline = time.monotonic() + 2
    while not started and time.monotonic() < deadline:
        time.sleep(0.01)
    assert started == [0.0]
    assert finished == []  # still running in the background

    release.append(True)
    executor.shutdown(wait=True)
    assert finished == [0.0]


def test_submit_tick_dispatches_to_the_shared_executor(monkeypatch):
    """submit_tick itself (not the generic Scheduler class) is what actually
    offloads a plugin's tick.py subprocess call to _TICK_EXECUTOR - confirm
    it does that rather than calling run_tick_subprocess inline."""
    import concurrent.futures

    import harness.scheduler as scheduler_module

    calls = []
    monkeypatch.setattr(
        scheduler_module, "run_tick_subprocess", lambda p: calls.append(p)
    )
    test_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    monkeypatch.setattr(scheduler_module, "_TICK_EXECUTOR", test_executor)

    submit_tick("some-plugin")
    test_executor.shutdown(wait=True)

    assert calls == ["some-plugin"]


def test_run_tick_subprocess_logs_unhandled_exception_instead_of_crashing_the_pool():
    """run_tick_subprocess runs inside a thread pool worker (via
    submit_tick) - an unhandled exception there would otherwise be silently
    swallowed by concurrent.futures unless something calls .result() on the
    future, which nothing does (fire-and-forget by design). Confirm it's
    caught and logged instead."""
    import io
    import contextlib

    from harness.scheduler import run_tick_subprocess

    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        # A plugin directory that doesn't exist makes subprocess.run's cwd=
        # argument raise FileNotFoundError before tick.py ever runs.
        run_tick_subprocess("this-plugin-directory-does-not-exist")

    assert "unhandled exception" in stderr.getvalue()
