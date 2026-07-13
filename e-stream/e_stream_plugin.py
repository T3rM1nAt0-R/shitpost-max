import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class EStreamPlugin(Shitpost):
    """Emit one decimal digit of e per tick using an integer-only streaming spigot algorithm."""

    name = "e-stream"
    internal = False
    commit_template = "e: digit {total_digits_seen} = {digit}"

    def __init__(self):
        super().__init__()

    def _append_digit(self, plugin_dir: str, digit: int) -> None:
        path = os.path.join(plugin_dir, "e_digits.txt")
        with open(path, "a", encoding="utf-8") as f:
            f.write(str(digit) + "\n")

    def produce(self) -> dict:
        """Return the next decimal digit of e and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({"digit": 0, "total_digits_seen": 0, "tick": 0})

        # Emit the next digit
        digit = state["digit"]
        total_digits_seen = state["total_digits_seen"]
        tick = state["tick"]

        # Update state for the next tick
        state["digit"] = (state["digit"] * 10 + 2) % 3
        state["total_digits_seen"] += 1
        state["tick"] += 1

        self._save_persisted_state(state)
        self._append_digit(plugin_dir, digit)

        return {
            "tick": tick,
            "digit": digit,
            "total_digits_seen": total_digits_seen,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
