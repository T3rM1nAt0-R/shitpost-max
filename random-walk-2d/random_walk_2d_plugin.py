"""AI-driven stochastic trajectory optimization platform for Monte Carlo reference architectures. Every step is a diversification strategy."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class RandomWalk2DPlugin(Shitpost):
    """Step a deterministic (LCG-seeded) 2D random walk one step per tick."""

    name = "random-walk-2d"
    internal = False
    commit_template = "walk step: ({x}, {y}), dist^2={distance_squared}"

    _A = 1103515245
    _C = 12345
    _M = 2 ** 31

    def produce(self) -> dict:
        """Return the next random-walk position and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "seed": 42,
            "x": 0,
            "y": 0,
            "tick": 0,
        })

        seed = (self._A * state["seed"] + self._C) % self._M
        direction = (seed >> 16) % 4

        x, y = state["x"], state["y"]
        if direction == 0:
            y += 1
        elif direction == 1:
            y -= 1
        elif direction == 2:
            x += 1
        else:
            x -= 1

        state["seed"] = seed
        state["x"] = x
        state["y"] = y
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "x": x,
            "y": y,
            "distance_squared": x * x + y * y,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
