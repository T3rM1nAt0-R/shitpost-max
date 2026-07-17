"""Revolutionizing streaming frequency estimation with a sub-linear AI-enhanced sketch data structure. Approximate counts are the new exact."""

import hashlib
import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class CountMinSketchPlugin(Shitpost):
    """Maintain a Count-Min Sketch over a fixed, cycling item stream."""

    name = "count-min-sketch"
    internal = False
    commit_template = "cms {item}: estimate={estimate} exact={exact}"

    _WIDTH = 8
    _DEPTH = 3
    _STREAM = ["apple", "banana", "apple", "cherry", "apple", "banana", "date", "apple"]

    @classmethod
    def _hash(cls, item: str, row: int) -> int:
        digest = hashlib.md5(f"{row}:{item}".encode()).hexdigest()
        return int(digest, 16) % cls._WIDTH

    def produce(self) -> dict:
        """Return the current item's sketch estimate and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "counters": [[0] * self._WIDTH for _ in range(self._DEPTH)],
            "exact_counts": {},
            "position": 0,
            "tick": 0,
        })

        item = self._STREAM[state["position"] % len(self._STREAM)]

        for row in range(self._DEPTH):
            col = self._hash(item, row)
            state["counters"][row][col] += 1

        estimate = min(state["counters"][row][self._hash(item, row)] for row in range(self._DEPTH))
        state["exact_counts"][item] = state["exact_counts"].get(item, 0) + 1
        exact = state["exact_counts"][item]

        state["position"] += 1
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "item": item,
            "estimate": estimate,
            "exact": exact,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
