"""AI-driven evolutionary computation platform for goal-directed string optimization. Every generation is a fitness-maximizing pivot."""

import os
import string
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class GeneticHelloPlugin(Shitpost):
    """Evolve a string toward a target phrase via deterministic (LCG-driven) hill-climbing."""

    name = "genetic-hello"
    internal = False
    commit_template = "genetic gen {tick}: {current} (fitness {fitness})"

    _A = 1103515245
    _C = 12345
    _M = 2 ** 31
    _TARGET = "HI"
    _ALPHABET = string.ascii_uppercase

    def _next_seed(self, seed: int) -> int:
        return (self._A * seed + self._C) % self._M

    @classmethod
    def _fitness(cls, s: str) -> int:
        return sum(1 for a, b in zip(s, cls._TARGET) if a == b)

    def produce(self) -> dict:
        """Attempt one mutation and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "seed": 42,
            "current": "AA",
            "tick": 0,
        })

        seed = self._next_seed(state["seed"])
        pos = (seed >> 8) % len(self._TARGET)
        seed = self._next_seed(seed)
        letter = self._ALPHABET[(seed >> 8) % 26]

        current = state["current"]
        cur_fit = self._fitness(current)
        candidate = current[:pos] + letter + current[pos + 1:]
        cand_fit = self._fitness(candidate)

        if cand_fit >= cur_fit:
            current = candidate
            cur_fit = cand_fit

        state["seed"] = seed
        state["current"] = current
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "current": current,
            "fitness": cur_fit,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
