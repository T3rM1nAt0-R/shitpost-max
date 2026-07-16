"""AI-optimized wildfire propagation modeling platform for enterprise risk analytics. Every burned cell is a derisked asset."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class ForestFireSimPlugin(Shitpost):
    """Run one generation of a forest fire cellular automaton per tick, resetting once the fire dies out."""

    name = "forest-fire-sim"
    internal = False
    commit_template = "fire gen {tick}: {trees} trees, {burning} burning, {empty} empty"

    _WIDTH = 6
    _HEIGHT = 6

    @classmethod
    def _initial_grid(cls) -> list:
        grid = [["T"] * cls._WIDTH for _ in range(cls._HEIGHT)]
        grid[0][0] = "B"
        return grid

    @classmethod
    def _step(cls, grid: list) -> list:
        new_grid = [row[:] for row in grid]
        for y in range(cls._HEIGHT):
            for x in range(cls._WIDTH):
                if grid[y][x] == "B":
                    new_grid[y][x] = "."
                elif grid[y][x] == "T":
                    for dy in (-1, 0, 1):
                        found = False
                        for dx in (-1, 0, 1):
                            if dx == 0 and dy == 0:
                                continue
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < cls._HEIGHT and 0 <= nx < cls._WIDTH and grid[ny][nx] == "B":
                                new_grid[y][x] = "B"
                                found = True
                                break
                        if found:
                            break
        return new_grid

    def produce(self) -> dict:
        """Advance the fire simulation one generation and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "grid": self._initial_grid(),
            "tick": 0,
        })

        new_grid = self._step(state["grid"])
        trees = sum(row.count("T") for row in new_grid)
        burning = sum(row.count("B") for row in new_grid)
        empty = sum(row.count(".") for row in new_grid)

        state["grid"] = self._initial_grid() if burning == 0 else new_grid
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "trees": trees,
            "burning": burning,
            "empty": empty,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
