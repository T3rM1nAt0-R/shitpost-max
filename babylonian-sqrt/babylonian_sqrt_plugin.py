"""Revolutionized iterative approximation with an AI-enhanced Babylonian convergence engine. Each tick is one step closer to quadratic perfection."""

import math
import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class BabylonianSqrtPlugin(Shitpost):
    """Perform one Newton-Raphson (Babylonian) iteration per tick to approximate a square root."""

    name = "babylonian-sqrt"
    internal = False
    commit_template = "babylonian sqrt({n}) iter {iteration}: {approximation}"

    _MAX_ITERATIONS = 20
    _CONVERGED_TOLERANCE = 1e-12

    @staticmethod
    def _is_perfect_square(n: int) -> bool:
        r = math.isqrt(n)
        return r * r == n

    def _next_target(self, n: int) -> int:
        candidate = n + 1
        while self._is_perfect_square(candidate):
            candidate += 1
        return candidate

    def produce(self) -> dict:
        """Return the current Babylonian-method approximation and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "n": 2,
            "x": 1.0,
            "iterations": 0,
            "tick": 0,
        })

        n = state["n"]
        x = 0.5 * (state["x"] + n / state["x"])
        state["iterations"] += 1
        converged = abs(x * x - n) < self._CONVERGED_TOLERANCE

        iteration = state["iterations"]
        state["x"] = x

        if converged or state["iterations"] >= self._MAX_ITERATIONS:
            state["n"] = self._next_target(n)
            state["x"] = state["n"] / 2.0
            state["iterations"] = 0

        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "n": n,
            "approximation": x,
            "iteration": iteration,
            "converged": converged,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
