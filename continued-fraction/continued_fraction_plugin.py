"""Decentralized the irrational number representation space with an infinite continued fraction oracle. Every quotient is a micro-transaction in the math economy."""

import math
import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class ContinuedFractionPlugin(Shitpost):
    """Emit one continued-fraction term per tick for a rotating list of irrational constants."""

    name = "continued-fraction"
    internal = False
    commit_template = "continued fraction {constant}: term {term_index} = {term}"

    _MAX_TERMS = 15
    _CONSTANTS = [
        ("sqrt(2)", 2 ** 0.5),
        ("sqrt(3)", 3 ** 0.5),
        ("sqrt(5)", 5 ** 0.5),
        ("phi", (1 + 5 ** 0.5) / 2),
        ("sqrt(6)", 6 ** 0.5),
        ("sqrt(7)", 7 ** 0.5),
    ]

    def produce(self) -> dict:
        """Return the next continued-fraction term and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        _, x0 = self._CONSTANTS[0]
        state = self._load_persisted_state({
            "constant_index": 0,
            "x": x0,
            "term_count": 0,
            "tick": 0,
        })

        constant_name, _ = self._CONSTANTS[state["constant_index"]]
        x = state["x"]
        a = math.floor(x)

        term_index = state["term_count"]
        state["x"] = 1 / (x - a)
        state["term_count"] += 1

        if state["term_count"] >= self._MAX_TERMS:
            state["constant_index"] = (state["constant_index"] + 1) % len(self._CONSTANTS)
            state["x"] = self._CONSTANTS[state["constant_index"]][1]
            state["term_count"] = 0

        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "constant": constant_name,
            "term": a,
            "term_index": term_index,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
