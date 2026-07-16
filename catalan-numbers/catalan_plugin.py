"""Counted every way to parenthesize an expression so you don't have to. One full Catalan number per tick, zero regrets."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost, summarize_big_int


class CatalanNumbersPlugin(Shitpost):
    """Emit one full Catalan number per tick."""

    name = "catalan-numbers"
    internal = False
    commit_template = "catalan C({n}): {catalan}"

    def __init__(self):
        super().__init__()
        self._numbers_file_name = "catalan.txt"

    def _persisted_state_path(self) -> str:
        """Keep the original state filename to preserve existing state."""
        return os.path.join(self._plugin_dir(), "catalan_state.json")

    def _append_number(self, plugin_dir: str, number: int) -> None:
        path = os.path.join(plugin_dir, self._numbers_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(str(number) + "\n")

    def produce(self) -> dict:
        """Return the next Catalan number and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({"n": 0, "current_catalan": 1, "tick": 0})

        # Emit the current catalan number.
        catalan = state["current_catalan"]
        n = state["n"]

        # Advance to the next catalan number using the recurrence relation.
        if n > 0:
            state["current_catalan"] = (state["current_catalan"] * 2 * (2 * n + 1)) // (n + 2)

        state["tick"] += 1
        state["n"] += 1

        self._save_persisted_state(state)
        self._append_number(plugin_dir, catalan)

        return {
            "tick": state["tick"],
            "n": n,
            "catalan": summarize_big_int(catalan),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
