"""Disrupting the multiplicative number theory landscape with real-time Möbius inversion analysis. Every -1, 0, or 1 is a mathematically significant insight."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class MobiusFunctionPlugin(Shitpost):
    """Compute the Möbius function mu(n) for consecutive positive integers."""

    name = "mobius-function"
    internal = False
    commit_template = "mobius({n}) = {mobius}"

    @staticmethod
    def _mobius(n: int) -> int:
        if n == 1:
            return 1
        distinct_primes = 0
        p = 2
        while p * p <= n:
            if n % p == 0:
                n //= p
                distinct_primes += 1
                if n % p == 0:
                    return 0
            p += 1
        if n > 1:
            distinct_primes += 1
        return (-1) ** distinct_primes

    def produce(self) -> dict:
        """Return the Mobius function value for the current candidate and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "n": 1,
            "tick": 0,
        })

        n = state["n"]
        mobius = self._mobius(n)

        state["n"] += 1
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "n": n,
            "mobius": mobius,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
