"""AI-driven decision-theory platform for optimal switching strategy research. Every trial is a statistically significant insight."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class MontyHallSimPlugin(Shitpost):
    """Simulate Monty Hall trials via a deterministic LCG, tracking stay vs switch win rates."""

    name = "monty-hall-sim"
    internal = False
    commit_template = "monty hall: stay={stay_rate} switch={switch_rate} (n={trials})"

    _A = 1103515245
    _C = 12345
    _M = 2 ** 31

    def _next_seed(self, seed: int) -> int:
        return (self._A * seed + self._C) % self._M

    def produce(self) -> dict:
        """Run one Monty Hall trial and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "seed": 42,
            "stay_wins": 0,
            "switch_wins": 0,
            "trials": 0,
            "tick": 0,
        })

        seed = self._next_seed(state["seed"])
        car = (seed >> 8) % 3
        seed = self._next_seed(seed)
        pick = (seed >> 8) % 3

        host_reveal = next(d for d in range(3) if d != pick and d != car)
        switch_door = next(d for d in range(3) if d != pick and d != host_reveal)

        if pick == car:
            state["stay_wins"] += 1
        if switch_door == car:
            state["switch_wins"] += 1

        state["seed"] = seed
        state["trials"] += 1
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "trials": state["trials"],
            "stay_wins": state["stay_wins"],
            "switch_wins": state["switch_wins"],
            "stay_rate": state["stay_wins"] / state["trials"],
            "switch_rate": state["switch_wins"] / state["trials"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
