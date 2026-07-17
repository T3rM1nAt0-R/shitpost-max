"""AI-driven compartmental epidemiological modeling platform for pandemic-adjacent risk analytics. Every recovery is a public health KPI."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class EpidemicSimPlugin(Shitpost):
    """Run one day of a discrete SIR epidemic model on a fixed population per tick."""

    name = "epidemic-sim"
    internal = False
    commit_template = "epidemic day {day}: S={s} I={i} R={r}"

    _N = 1000
    _BETA = 0.3
    _GAMMA = 0.1

    def produce(self) -> dict:
        """Advance the SIR model one day and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "s": 990.0,
            "i": 10.0,
            "r": 0.0,
            "day": 0,
            "tick": 0,
        })

        s, i, r = state["s"], state["i"], state["r"]
        new_infections = self._BETA * s * i / self._N
        new_recoveries = self._GAMMA * i

        # Keep full float precision in persisted state -- rounding before
        # persisting compounds across ticks and drifts from the true
        # sequence (verified directly, same class of bug as sierpinski-chaos).
        s = s - new_infections
        i = i + new_infections - new_recoveries
        r = r + new_recoveries

        state["s"], state["i"], state["r"] = s, i, r
        state["day"] += 1
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "day": state["day"],
            "s": round(s, 2),
            "i": round(i, 2),
            "r": round(r, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
