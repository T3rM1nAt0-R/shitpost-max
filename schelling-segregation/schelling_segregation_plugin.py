"""AI-driven agent-based urban dynamics platform modeling emergent segregation patterns. Every relocation is a market-clearing decision."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class SchellingSegregationPlugin(Shitpost):
    """Run one tick of Schelling's segregation model on a fixed 5x5 grid."""

    name = "schelling-segregation"
    internal = False
    commit_template = "schelling gen {tick}: {moves} moves"

    _INITIAL_GRID = ["AB.AB", "BA.BA", ".....", "AB.AB", "BA.BA"]

    def produce(self) -> dict:
        """Run one tick of the segregation model and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "grid": [list(row) for row in self._INITIAL_GRID],
            "tick": 0,
        })

        grid = state["grid"]
        h = len(grid)
        w = len(grid[0])

        empties = [(y, x) for y in range(h) for x in range(w) if grid[y][x] == "."]
        new_grid = [row[:] for row in grid]
        moves = 0

        for y in range(h):
            for x in range(w):
                cell = grid[y][x]
                if cell == ".":
                    continue
                same = 0
                total = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w and grid[ny][nx] != ".":
                            total += 1
                            if grid[ny][nx] == cell:
                                same += 1
                if total > 0 and (same / total) < 0.5 and empties:
                    ty, tx = empties.pop(0)
                    new_grid[ty][tx] = cell
                    new_grid[y][x] = "."
                    empties.append((y, x))
                    moves += 1

        state["grid"] = new_grid
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "moves": moves,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
