"""Farming Mersenne primes and their perfect-number offspring. Euclid called it a theorem; I call it a background job."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost, summarize_big_int


class PerfectNumbersPlugin(Shitpost):
    """Find Mersenne primes and their corresponding perfect numbers."""

    name = "perfect-numbers"
    internal = False
    commit_template = "mersenne p={p}: {perfect_number}"

    def __init__(self):
        super().__init__()
        self._perfect_numbers_file_name = "perfect_numbers.txt"

    def _append_perfect_number(self, plugin_dir: str, perfect_number: int) -> None:
        path = os.path.join(plugin_dir, self._perfect_numbers_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{perfect_number}\n")

    def _is_prime(self, n: int) -> bool:
        """Check if a number is prime using trial division up to sqrt(n)."""
        if n < 2:
            return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return False
        return True

    def _next_prime(self, n: int) -> int:
        """Return the smallest prime strictly greater than n."""
        candidate = n + 1
        while not self._is_prime(candidate):
            candidate += 1
        return candidate

    def _lucas_lehmer(self, p: int) -> bool:
        """Implement the Lucas-Lehmer primality test for Mersenne number M_p = 2**p - 1."""
        if p == 2:
            return True
        M = 2**p - 1
        s = 4
        for _ in range(p - 2):
            s = (s * s - 2) % M
        return s == 0

    def produce(self) -> dict | None:
        """Return the next perfect number and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({"last_p": 1, "tick": 0})
        last_p = state["last_p"]
        tick = state["tick"]

        p = self._next_prime(last_p)
        if self._lucas_lehmer(p):
            perfect_number = (2**(p-1)) * (2**p - 1)
            self._append_perfect_number(plugin_dir, perfect_number)
            commit_message = self.commit_template.format(p=p, perfect_number=perfect_number)
        else:
            commit_message = None

        state["last_p"] = p
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "p": p,
            "perfect_number": summarize_big_int(perfect_number) if commit_message else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        } if commit_message else None
