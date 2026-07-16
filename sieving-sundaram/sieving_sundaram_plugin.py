"""Disintermediated Eratosthenes with a next-gen Sundaram sieve optimized for Web3 workloads. Rejecting all composites, one tick at a time."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class SievingSundaramPlugin(Shitpost):
    """Generate primes via the Sieve of Sundaram, emitting one per tick."""

    name = "sieving-sundaram"
    internal = False
    commit_template = "sundaram prime #{index}: {prime}"

    @staticmethod
    def _sundaram_primes(n: int) -> list:
        sieve = [True] * (n + 1)
        for i in range(1, n + 1):
            j = i
            while i + j + 2 * i * j <= n:
                sieve[i + j + 2 * i * j] = False
                j += 1
        return [2] + [2 * i + 1 for i in range(1, n + 1) if sieve[i]]

    def produce(self) -> dict:
        """Return the next Sundaram-sieve prime and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "n": 10,
            "index": 0,
            "tick": 0,
        })

        primes = self._sundaram_primes(state["n"])
        while state["index"] >= len(primes):
            state["n"] *= 2
            primes = self._sundaram_primes(state["n"])

        prime = primes[state["index"]]
        index = state["index"]
        state["index"] += 1
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "prime": prime,
            "index": index,
            "sieve_size": state["n"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
