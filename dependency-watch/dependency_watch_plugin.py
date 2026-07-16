"""Tracks a fixed embedded history of dependency counts, cycling through snapshots and showing the delta."""

from harness.shitpost_base import Shitpost

HISTORY = [
    ("2026-01-01", 12),
    ("2026-02-01", 15),
    ("2026-03-01", 15),
    ("2026-04-01", 19),
    ("2026-05-01", 22),
]


class DependencyWatchPlugin(Shitpost):
    """Emit one HISTORY snapshot per tick, cycling through the list."""

    name = "dependency-watch"
    internal = False
    commit_template = "deps {snapshot_date}: {dependency_count} ({delta:+d})"

    def produce(self) -> dict:
        state = self._load_persisted_state({"index": 0})
        index = state["index"]

        date, count = HISTORY[index]
        delta = 0 if index == 0 else count - HISTORY[index - 1][1]

        result = {
            "snapshot_date": date,
            "dependency_count": count,
            "delta": delta,
        }

        self._save_persisted_state({"index": (index + 1) % len(HISTORY)})

        return result
