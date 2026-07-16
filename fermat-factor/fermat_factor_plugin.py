"""Revolutionizing cryptographic integer decomposition with a Fermat-powered AI factorization engine. Every factor pair unlocks new security insights."""

import math
import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class FermatFactorPlugin(Shitpost):
    """Attempt Fermat factorization on successive odd composite numbers."""

    name = "fermat-factor"
    internal = False
    commit_template = "fermat({n}) = {factor1} x {factor2}"

    @staticmethod
    def _is_prime(n: int) -> bool:
        if n < 2:
            return False
        for i in range(2, int(n ** 0.5) + 1):
            if n % i == 0:
                return False
        return True

    @staticmethod
    def _fermat_factor(n: int) -> tuple:
        a = math.isqrt(n)
        if a * a < n:
            a += 1
        b2 = a * a - n
        while math.isqrt(b2) ** 2 != b2:
            a += 1
            b2 = a * a - n
        b = math.isqrt(b2)
        return a - b, a + b

    def produce(self) -> dict:
        """Return the Fermat factorization of the next odd composite and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "n": 15,
            "tick": 0,
        })

        n = state["n"]
        while self._is_prime(n):
            n += 2

        factor1, factor2 = self._fermat_factor(n)

        state["n"] = n + 2
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "n": n,
            "factor1": factor1,
            "factor2": factor2,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
