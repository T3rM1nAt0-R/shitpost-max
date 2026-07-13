import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class Sqrt2SpigotPlugin(Shitpost):
    """Emit one decimal digit of sqrt(2) per tick."""

    name = "sqrt2-stream"
    internal = False
    commit_template = "sqrt2: digit {total_digits_seen} = {digit}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "spigot_state.json"
        self._digits_file_name = "sqrt2_digits.txt"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running spigot state, or initialise it for the first tick."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: spigot state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            required = {
                "r",
                "c",
                "tick",
                "total_digits_seen",
            }
            if not required.issubset(state.keys()):
                print(
                    "warning: spigot state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        # Start with the initial values for sqrt(2) spigot algorithm
        return {
            "r": 2,
            "c": 0,
            "tick": 0,
            "total_digits_seen": 0,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _append_digit(self, plugin_dir: str, digit: int) -> None:
        path = os.path.join(plugin_dir, self._digits_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(str(digit))

    def produce(self) -> dict:
        """Return the next digit of sqrt(2) and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        r, c = state["r"], state["c"]

        d = 0
        while (20 * c + d) * d <= r:
            d += 1

        d -= 1
        self._append_digit(plugin_dir, d)

        state["r"] = r - (20 * c + d) * d
        state["c"] = 10 * c + d
        state["r"] *= 100
        state["tick"] += 1
        state["total_digits_seen"] += 1

        self._save_state(plugin_dir, state)

        return {
            "tick": state["tick"],
            "digit": d,
            "total_digits_seen": state["total_digits_seen"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
