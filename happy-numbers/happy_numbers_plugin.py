"""AI-powered happiness detector for the integer community. Quantifying numerical well-being through iterative square-sum meditation."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class HappyNumbersPlugin(Shitpost):
    """Scan consecutive integers for happy numbers, emitting each one found."""

    name = "happy-numbers"
    internal = False
    commit_template = "happy number found: {happy_number}"

    _SCAN_CAP = 1000

    @staticmethod
    def _is_happy(n: int) -> bool:
        seen = set()
        while n != 1 and n not in seen:
            seen.add(n)
            n = sum(int(d) ** 2 for d in str(n))
        return n == 1

    def produce(self) -> dict | None:
        """Return the next happy number found and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "candidate": 1,
            "tick": 0,
        })

        start = state["candidate"]
        found = None
        for n in range(start, start + self._SCAN_CAP):
            if self._is_happy(n):
                found = n
                break

        state["tick"] += 1

        if found is None:
            state["candidate"] = start + self._SCAN_CAP
            self._save_persisted_state(state)
            return None

        state["candidate"] = found + 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "happy_number": found,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
