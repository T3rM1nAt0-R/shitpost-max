"""Hunting twin primes at scale so mathematicians can retire. Streaming pairs, zero conjectures actually resolved."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class TwinPrimesPlugin(Shitpost):
    """Find twin prime pairs."""

    name = "twin-primes"
    internal = False
    commit_template = "candidate {candidate}: {twin}"

    def __init__(self):
        super().__init__()
        self._twins_file_name = "twins.txt"

    def _append_twin(self, plugin_dir: str, last_prime: int, candidate: int) -> None:
        path = os.path.join(plugin_dir, self._twins_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"twin: ({last_prime}, {candidate})\n")

    def _is_prime(self, n: int) -> bool:
        """Check if a number is prime using trial division up to sqrt(n)."""
        if n < 2:
            return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return False
        return True

    def produce(self) -> dict | None:
        """Return the next twin prime pair and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({"last_prime": 2, "candidate": 3, "tick": 0})
        last_prime = state["last_prime"]
        candidate = state["candidate"]

        commit_message = None
        if self._is_prime(candidate):
            if candidate - last_prime == 2:
                self._append_twin(plugin_dir, last_prime, candidate)
                commit_message = self.commit_template.format(candidate=candidate, twin=f"({last_prime}, {candidate})")
                state["last_prime"] = candidate
            else:
                state["last_prime"] = candidate

        state["candidate"] += 2
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],  # post-increment, matches collatz-explorer's convention
            "candidate": candidate,
            "twin": [last_prime, candidate] if commit_message else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        } if commit_message else None
