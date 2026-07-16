"""Reverse-engineered the golden ratio from first principles (Gibbons already did it in 1985, I just run his code). One φ digit per tick, infinite aesthetic.

Uses the continued-fraction convergents of φ = [1; 1, 1, 1, ...].
The recurrence is the Fibonacci recurrence:

    p_{-1} = 1, p_0 = 1, q_{-1} = 0, q_0 = 1
    p_n = p_{n-1} + p_{n-2}
    q_n = q_{n-1} + q_{n-2}

so p_n/q_n = F_{n+1}/F_n approaches φ from alternating sides.

The internal state is persisted in ``spigot_state.json`` so each tick
resumes where the previous one left off.  A new digit is emitted only
when two successive convergents agree on the next unclaimed decimal
digit.
"""

import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class PhiSpigotPlugin(Shitpost):
    """Emit one decimal digit of φ per tick."""

    name = "golden-ratio"
    internal = False
    commit_template = "φ: digit {total_digits_seen} = {digit} (convergent {convergent_n})"

    def __init__(self):
        super().__init__()
        self._state_file_name = "spigot_state.json"
        self._digits_file_name = "phi_digits.txt"

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
                "p_prev",
                "q_prev",
                "p_curr",
                "q_curr",
                "n",
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
        # Start with the first two convergents that are safe to divide:
        # 1/1 (n=0) and 2/1 (n=1).  The next advances produce 3/2, 5/3, ...
        return {
            "p_prev": 1,
            "q_prev": 1,
            "p_curr": 2,
            "q_curr": 1,
            "n": 1,
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
    def _scaled_floor(p: int, q: int, position: int) -> int:
        """Return floor((p/q) * 10**position) as an integer.

        Position 0 is the units digit, position 1 is the first digit after
        the decimal point, and so on. The digit AT ``position`` is this
        floor's value mod 10 (see ``_next_digit``) - comparing the full
        floor, not just that one digit, is required for correctness: two
        convergents can agree on the digit at a position while disagreeing
        on a higher-significance digit (e.g. 1/1 and 2/1 both have digit 0
        at position 1, yet neither is close to phi's real first decimal
        digit, 6 - flagged and confirmed correct behavior in DeepSeek
        review, 2026-07-10).
        """
        return p * 10**position // q

    def _next_digit(self, state: dict) -> int:
        """Advance the convergent recurrence until the next digit stabilises.

        The state dictionary is mutated in place and the digit is returned.
        """
        while True:
            position = state["total_digits_seen"]
            prev_floor = self._scaled_floor(
                state["p_prev"], state["q_prev"], position
            )
            curr_floor = self._scaled_floor(
                state["p_curr"], state["q_curr"], position
            )

            if prev_floor == curr_floor:
                return curr_floor % 10

            # Advance the recurrence: p_n = p_{n-1} + p_{n-2}.
            p_next = state["p_prev"] + state["p_curr"]
            q_next = state["q_prev"] + state["q_curr"]
            state["p_prev"] = state["p_curr"]
            state["q_prev"] = state["q_curr"]
            state["p_curr"] = p_next
            state["q_curr"] = q_next
            state["n"] += 1

    def produce(self) -> dict:
        """Return the next digit of φ and update persistent files."""
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
            "convergent_n": state["n"],
            "total_digits_seen": state["total_digits_seen"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
