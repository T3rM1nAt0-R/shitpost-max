"""Proved sqrt(2) is irrational (again) one digit per tick. Pythagoras workshopped this for years; I automated it before lunch."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class Sqrt2SpigotPlugin(Shitpost):
    """Emit one decimal digit of sqrt(2) per tick."""

    name = "sqrt2-stream"
    internal = False
    commit_template = "sqrt2: digit {total_digits_seen} = {digit}"

    def __init__(self):
        super().__init__()
        self._digits_file_name = "sqrt2_digits.txt"

    def _persisted_state_path(self) -> str:
        return os.path.join(self._plugin_dir(), "spigot_state.json")

    def _append_digit(self, plugin_dir: str, digit: int) -> None:
        path = os.path.join(plugin_dir, self._digits_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(str(digit))

    def produce(self) -> dict:
        """Return the next digit of sqrt(2) and update persistent files."""
        state = self._load_persisted_state({
            "r": 2,
            "c": 0,
            "tick": 0,
            "total_digits_seen": 0,
        })
        r, c = state["r"], state["c"]

        d = 0
        while (20 * c + d) * d <= r:
            d += 1

        d -= 1
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)
        self._append_digit(plugin_dir, d)

        state["r"] = r - (20 * c + d) * d
        state["c"] = 10 * c + d
        state["r"] *= 100
        state["tick"] += 1
        state["total_digits_seen"] += 1

        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "digit": d,
            "total_digits_seen": state["total_digits_seen"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
