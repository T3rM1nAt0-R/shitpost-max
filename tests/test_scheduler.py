from harness.scheduler import Scheduler


class FakeClock:
    """A controllable clock: advances only when told to, never real time."""

    def __init__(self, start=0.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def make_scheduler(plugins, clock, run_log):
    def fake_run_tick(plugin_dir):
        run_log.append((clock.now, plugin_dir))

    def fake_sleep(seconds):
        # A real scheduler would block for `seconds`; the test just
        # advances the fake clock by the same amount instead of waiting.
        clock.advance(seconds)

    return Scheduler(plugins, run_tick=fake_run_tick, clock=clock, sleeper=fake_sleep)


def test_step_runs_soonest_due_plugin_first():
    clock = FakeClock(start=100.0)
    run_log = []
    scheduler = make_scheduler(
        [("slow", 600), ("fast", 60)], clock=clock, run_log=run_log
    )

    # Both start "due now" - heap order among equal due-times falls back to
    # plugin_dir string comparison, so this just confirms step() runs one
    # of them without erroring and returns its name.
    ran = scheduler.step()
    assert ran in ("slow", "fast")
    assert run_log == [(100.0, ran)]


def test_faster_cadence_plugin_runs_more_often():
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
    run_log = []
    # A run_tick that "takes 5 seconds" - the clock advances mid-tick,
    # simulating a slow subprocess, so we can check the next due time isn't
    # computed from *after* that delay.
    calls = []

    def slow_run_tick(plugin_dir):
        calls.append(clock.now)
        clock.advance(5.0)  # tick itself takes 5s

    scheduler = Scheduler(
        [("only", 60)], run_tick=slow_run_tick, clock=clock, sleeper=lambda s: clock.advance(s)
    )

    scheduler.step()  # runs at t=0, "takes" until t=5
    due_time, plugin_dir, cadence = scheduler._heap[0]
    # Must be due_time(0) + cadence(60) = 60, not now(5) + cadence(60) = 65 -
    # otherwise a slow tick would permanently push every future tick later.
    assert due_time == 60


def test_two_plugins_never_collide_in_the_heap():
    """Sanity check that the heap always holds exactly one entry per plugin,
    regardless of how many steps run - nothing gets dropped or duplicated."""
    clock = FakeClock(start=0.0)
    run_log = []
    plugins = [("a", 7), ("b", 13), ("c", 5), ("d", 30)]
    scheduler = make_scheduler(plugins, clock=clock, run_log=run_log)

    for _ in range(50):
        scheduler.step()

    assert len(scheduler._heap) == len(plugins)
    heap_names = {entry[1] for entry in scheduler._heap}
    assert heap_names == {name for name, _ in plugins}
