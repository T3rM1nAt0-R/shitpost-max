"""Quantifying digital entropy through multiplicative collapse analysis. Each integer's persistence is a KPI for number wellness."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class MultiplicativePersistencePlugin(Shitpost):
    """Compute multiplicative persistence for consecutive non-negative integers."""

    name = "multiplicative-persistence"
    internal = False
    commit_template = "persistence({n}) = {persistence}"

    @staticmethod
    def _persistence(n: int) -> int:
        steps = 0
        while n >= 10:
            product = 1
            for digit in str(n):
                product *= int(digit)
            n = product
            steps += 1
        return steps

    def produce(self) -> dict:
        """Return the multiplicative persistence of the current candidate and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "candidate": 0,
            "tick": 0,
        })

        n = state["candidate"]
        persistence = self._persistence(n)

        state["candidate"] += 1
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "n": n,
            "persistence": persistence,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
