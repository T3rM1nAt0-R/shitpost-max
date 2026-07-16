"""AI-accelerated fractal generation platform via stochastic vertex-attraction dynamics. Every point is a self-similar market signal."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class SierpinskiChaosPlugin(Shitpost):
    """Perform one chaos-game iteration per tick using a deterministic LCG to pick the target vertex."""

    name = "sierpinski-chaos"
    internal = False
    commit_template = "chaos game: vertex {vertex} -> ({x}, {y})"

    _A = 1103515245
    _C = 12345
    _M = 2 ** 31
    _VERTICES = [(0.0, 0.0), (1.0, 0.0), (0.5, 0.866)]

    def _next_seed(self, seed: int) -> int:
        return (self._A * seed + self._C) % self._M

    def produce(self) -> dict:
        """Advance the chaos game one step and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "seed": 42,
            "x": 0.5,
            "y": 0.5,
            "tick": 0,
        })

        seed = self._next_seed(state["seed"])
        vi = (seed >> 16) % 3
        vx, vy = self._VERTICES[vi]
        # Keep full float precision in persisted state -- rounding before
        # persisting would compound across ticks and drift from the
        # full-precision sequence (verified directly: diverges by tick 8).
        # Only round for the emitted/display value.
        x = (state["x"] + vx) / 2
        y = (state["y"] + vy) / 2

        state["seed"] = seed
        state["x"] = x
        state["y"] = y
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "vertex": vi,
            "x": round(x, 4),
            "y": round(y, 4),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
