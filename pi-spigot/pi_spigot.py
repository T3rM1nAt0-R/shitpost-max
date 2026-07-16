"""Solved π to arbitrary precision using an AI-integrated eval loop. Emits one digit per tick because shipping fast means shipping small.

Uses Gibbons' unbounded integer-only spigot algorithm.  The algorithm's
internal state is persisted in ``spigot_state.json`` so each tick resumes
where the previous one left off.
"""

import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class PiSpigotPlugin(Shitpost):
    """Emit one decimal digit of π per tick."""

    name = "pi-spigot"
    internal = False
    commit_template = "pi: digit {n} = {d}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "spigot_state.json"
        self._digits_file_name = "pi_digits.txt"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running spigot state, or initialise it for digit 1."""
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
            # Guard against manual tampering / old versions.
            required = {"q", "r", "t", "k", "n", "l", "tick", "total_digits_seen"}
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
        return {
            "q": 1,
            "r": 0,
            "t": 1,
            "k": 1,
            "n": 3,
            "l": 3,
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

    @staticmethod
    def _next_digit(state: dict) -> int:
        """Advance the Gibbons spigot until the next decimal digit is ready.

        The state dictionary is mutated in place and the digit is returned.
        """
        while True:
            q = state["q"]
            r = state["r"]
            t = state["t"]
            k = state["k"]
            n = state["n"]
            l = state["l"]

            # Emit a digit when the current estimate is stable.
            if 4 * q + r - t < n * t:
                state["q"] = 10 * q
                state["r"] = 10 * (r - n * t)
                state["t"] = t
                state["k"] = k
                state["n"] = (10 * (3 * q + r)) // t - 10 * n
                state["l"] = l
                return n

            # Otherwise consume another term of the infinite product.
            state["q"] = q * k
            state["r"] = (2 * q + r) * l
            state["t"] = t * l
            state["k"] = k + 1
            state["n"] = (q * (7 * k + 2) + r * l) // (t * l)
            state["l"] = l + 2

    def produce(self) -> dict:
        """Return the next digit of π and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        digit = self._next_digit(state)

        state["tick"] += 1
        state["total_digits_seen"] += 1

        self._save_state(plugin_dir, state)
        self._append_digit(plugin_dir, digit)

        return {
            "tick": state["tick"],
            "digit": digit,
            "total_digits_seen": state["total_digits_seen"],
            "n": state["total_digits_seen"],
            "d": digit,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
