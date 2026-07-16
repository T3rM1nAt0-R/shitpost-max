"""Disrupting the cellular automata industry with an AI-driven life simulation platform. Every generation is a Board-level strategic pivot."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class ConwayLifePlugin(Shitpost):
    """Advance Conway's Game of Life one generation per tick on a fixed toroidal grid."""

    name = "conway-life"
    internal = False
    commit_template = "conway gen {generation}: {live_cells} live cells"

    _WIDTH = 5
    _HEIGHT = 5

    @classmethod
    def _initial_grid(cls) -> list:
        grid = [[0] * cls._WIDTH for _ in range(cls._HEIGHT)]
        grid[2][1] = grid[2][2] = grid[2][3] = 1
        return grid

    @classmethod
    def _step(cls, grid: list) -> list:
        new_grid = [[0] * cls._WIDTH for _ in range(cls._HEIGHT)]
        for y in range(cls._HEIGHT):
            for x in range(cls._WIDTH):
                neighbors = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        ny, nx = (y + dy) % cls._HEIGHT, (x + dx) % cls._WIDTH
                        neighbors += grid[ny][nx]
                if grid[y][x]:
                    new_grid[y][x] = 1 if neighbors in (2, 3) else 0
                else:
                    new_grid[y][x] = 1 if neighbors == 3 else 0
        return new_grid

    def produce(self) -> dict:
        """Return the next generation's live-cell count and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "grid": self._initial_grid(),
            "generation": 0,
            "tick": 0,
        })

        state["grid"] = self._step(state["grid"])
        state["generation"] += 1
        state["tick"] += 1
        live_cells = sum(sum(row) for row in state["grid"])
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "generation": state["generation"],
            "live_cells": live_cells,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
