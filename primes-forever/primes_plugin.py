"""Enumerating every prime number that will ever exist, forever, on a cron schedule. Infinite scale, infinite commits."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost, summarize_big_int


class PrimesForeverPlugin(Shitpost):
    """Find prime numbers forever."""

    name = "primes-forever"
    internal = False
    commit_template = "prime found: {prime}"

    def __init__(self):
        super().__init__()
        self._primes_file_name = "primes.txt"

    def _persisted_state_path(self) -> str:
        return os.path.join(self._plugin_dir(), "primes_state.json")

    def _append_prime(self, plugin_dir: str, prime: int) -> None:
        path = os.path.join(plugin_dir, self._primes_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{prime}\n")

    def _is_prime(self, n: int) -> bool:
        """Check if a number is prime using trial division up to sqrt(n)."""
        if n < 2:
            return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return False
        return True

    def produce(self) -> dict:
        """Return the next prime number and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "last_prime": 2,
            "candidate": 1,
            "tick": 0,
        })
        last_prime = state["last_prime"]
        candidate = state["candidate"]

        while not self._is_prime(candidate):
            candidate += 1

        self._append_prime(plugin_dir, candidate)
        commit_message = self.commit_template.format(prime=candidate)
        state["last_prime"] = candidate
        state["candidate"] = candidate + 1
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "prime": summarize_big_int(candidate),
            "candidate": summarize_big_int(candidate),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
