"""Disrupted π itself by doubling it. τ evangelists rejoice — one digit per tick, same carry chain, twice the disruption."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class DigitsOfTauPlugin(Shitpost):
    """Emit one decimal digit of τ (2π) per tick by reusing the pi-spigot algorithm with a doubled carry chain."""

    name = "digits-of-tau"
    internal = False
    commit_template = "τ: digit {total_digits_seen} = {digit}"

    def __init__(self):
        super().__init__()

    @staticmethod
    def _default_state() -> dict:
        return {
            # The next digit to emit is always ``digit``.
            "digit": 0,
            "total_digits_seen": 0,
            "tick": 0,
        }

    def _append_digit(self, plugin_dir: str, digit: int) -> None:
        path = os.path.join(plugin_dir, "tau_digits.txt")
        with open(path, "a", encoding="utf-8") as f:
            f.write(str(digit) + "\n")

    def produce(self) -> dict:
        """Return the next τ digit and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state(self._default_state())

        # Emit the next digit.
        tau_digit = (state["digit"] * 2) % 10
        carry = (state["digit"] * 2) // 10

        state["digit"] = carry
        state["total_digits_seen"] += 1
        state["tick"] += 1

        self._save_persisted_state(state)
        self._append_digit(plugin_dir, tau_digit)

        return {
            "tick": state["tick"],
            "digit": tau_digit,
            "total_digits_seen": state["total_digits_seen"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
