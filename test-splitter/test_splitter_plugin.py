"""Splits a fixed embedded test list into N parallel groups via greedy longest-first bin-packing, cycling."""

from harness.shitpost_base import Shitpost

TESTS = [
    ("test_auth.py", 12.0),
    ("test_models.py", 8.0),
    ("test_views.py", 15.0),
    ("test_utils.py", 3.0),
    ("test_api.py", 20.0),
    ("test_forms.py", 5.0),
    ("test_cache.py", 7.0),
    ("test_tasks.py", 10.0),
]
N_GROUPS = 3


def _split(tests, n):
    groups = [[] for _ in range(n)]
    totals = [0.0] * n
    for name, duration in sorted(tests, key=lambda t: -t[1]):
        idx = totals.index(min(totals))
        groups[idx].append(name)
        totals[idx] += duration
    return groups, totals


GROUPS, TOTALS = _split(TESTS, N_GROUPS)


class TestSplitterPlugin(Shitpost):
    """Emit one test group per tick, cycling through N_GROUPS groups."""

    name = "test-splitter"
    internal = False
    commit_template = "test-split group {group_index}: {total_seconds}s"

    def produce(self) -> dict:
        state = self._load_persisted_state({"index": 0})
        index = state["index"]

        result = {
            "group_index": index,
            "files": GROUPS[index],
            "total_seconds": TOTALS[index],
        }

        self._save_persisted_state({"index": (index + 1) % N_GROUPS})

        return result
