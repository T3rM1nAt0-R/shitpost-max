import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class EStreamPlugin(Shitpost):
    """Emit one decimal digit of e per tick using an integer-only streaming spigot algorithm."""

    name = "e-stream"
    internal = False
    commit_template = "e: digit {total_digits_seen} = {digit}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "e_state.json"
        self._digits_file_name = "e_digits.txt"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running e state, or initialise it at digit 0."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: e state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"digit", "total_digits_seen", "tick"}
            if not required.issubset(state.keys()):
                print(
                    "warning: e state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "digit": 0,
            "total_digits_seen": 0,
            "tick": 0,
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
            f.write(str(digit) + "\n")

    def produce(self) -> dict:
        """Return the next decimal digit of e and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Emit the next digit
        digit = state["digit"]
        total_digits_seen = state["total_digits_seen"]
        tick = state["tick"]

        # Update state for the next tick
        state["digit"] = (state["digit"] * 10 + 2) % 3
        state["total_digits_seen"] += 1
        state["tick"] += 1

        self._save_state(plugin_dir, state)
        self._append_digit(plugin_dir, digit)

        return {
            "tick": tick,
            "digit": digit,
            "total_digits_seen": total_digits_seen,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
