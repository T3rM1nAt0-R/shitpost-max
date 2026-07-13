import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class DigitsOfTauPlugin(Shitpost):
    """Emit one decimal digit of τ (2π) per tick by reusing the pi-spigot algorithm with a doubled carry chain."""

    name = "digits-of-tau"
    internal = False
    commit_template = "τ: digit {total_digits_seen} = {digit}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "tau_state.json"
        self._digits_file_name = "tau_digits.txt"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running τ state, or initialise it at digit 0."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: τ state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"digit", "total_digits_seen", "tick"}
            if not required.issubset(state.keys()):
                print(
                    "warning: τ state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            # The next digit to emit is always ``digit``.
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
        """Return the next τ digit and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Emit the next digit.
        tau_digit = (state["digit"] * 2) % 10
        carry = (state["digit"] * 2) // 10

        state["digit"] = carry
        state["total_digits_seen"] += 1
        state["tick"] += 1

        self._save_state(plugin_dir, state)
        self._append_digit(plugin_dir, tau_digit)

        return {
            "tick": state["tick"],
            "digit": tau_digit,
            "total_digits_seen": state["total_digits_seen"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
