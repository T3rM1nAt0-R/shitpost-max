"""Revolutionizing emergent behavior analytics with an AI-powered universal Turing machine on a grid. Every ant step is an IPO milestone."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class LangtonAntPlugin(Shitpost):
    """Run one step of Langton's Ant on a bounded toroidal grid per tick."""

    name = "langton-ant"
    internal = False
    commit_template = "langton step {tick}: ({x},{y}), {black_cells} black"

    _SIZE = 20

    def produce(self) -> dict:
        """Advance Langton's Ant one step and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "grid": [[0] * self._SIZE for _ in range(self._SIZE)],
            "x": self._SIZE // 2,
            "y": self._SIZE // 2,
            "dx": 0,
            "dy": -1,
            "tick": 0,
        })

        x, y, dx, dy = state["x"], state["y"], state["dx"], state["dy"]
        if state["grid"][y][x] == 0:
            dx, dy = -dy, dx
            state["grid"][y][x] = 1
        else:
            dx, dy = dy, -dx
            state["grid"][y][x] = 0

        x = (x + dx) % self._SIZE
        y = (y + dy) % self._SIZE

        state["x"], state["y"], state["dx"], state["dy"] = x, y, dx, dy
        state["tick"] += 1
        black_cells = sum(sum(row) for row in state["grid"])
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "x": x,
            "y": y,
            "black_cells": black_cells,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
