"""Revolutionized the rational enumeration sector with an AI-driven Stern-Brocot traversal algorithm. Every fraction is a market-disrupting ratio."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class SternBrocotPlugin(Shitpost):
    """Enumerate Stern-Brocot tree fractions in breadth-first order, one per tick."""

    name = "stern-brocot"
    internal = False
    commit_template = "stern-brocot: {numerator}/{denominator}"

    def produce(self) -> dict:
        """Return the next Stern-Brocot fraction and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "queue": [[[0, 1], [1, 0]]],
            "tick": 0,
        })

        lo, hi = state["queue"].pop(0)
        mediant = [lo[0] + hi[0], lo[1] + hi[1]]

        state["queue"].append([lo, mediant])
        state["queue"].append([mediant, hi])
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "numerator": mediant[0],
            "denominator": mediant[1],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
