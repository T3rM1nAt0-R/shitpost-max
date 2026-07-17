"""Lists a fixed embedded set of branches by days-since-last-commit, sorted most-stale-first, cycling."""

from harness.shitpost_base import Shitpost

BRANCHES = [
    ("main", 0),
    ("feature/dark-mode", 3),
    ("fix/login-bug", 12),
    ("experiment/rewrite", 145),
    ("archive/old-api", 400),
]
SORTED = sorted(BRANCHES, key=lambda b: -b[1])


class BranchAgeTrackerPlugin(Shitpost):
    """Emit one SORTED entry per tick, cycling through the list."""

    name = "branch-age-tracker"
    internal = False
    commit_template = "branch-age {branch}: {days_stale}d"

    def produce(self) -> dict:
        state = self._load_persisted_state({"index": 0})
        index = state["index"]

        branch, days = SORTED[index]

        result = {
            "branch": branch,
            "days_stale": days,
        }

        self._save_persisted_state({"index": (index + 1) % len(SORTED)})

        return result
