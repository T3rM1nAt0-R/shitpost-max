import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class PrimesForeverPlugin(Shitpost):
    """Find prime numbers forever."""

    name = "primes-forever"
    internal = False
    commit_template = "prime found: {prime}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "primes_state.json"
        self._primes_file_name = "primes.txt"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running primes state, or initialise it for the first tick."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: primes state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            required = {
                "last_prime",
                "candidate",
                "tick",
            }
            if not required.issubset(state.keys()):
                print(
                    "warning: primes state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        # Start with last_prime=2, candidate=1 (next number to test is 3), and tick=0
        return {
            "last_prime": 2,
            "candidate": 1,
            "tick": 0,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

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

        state = self._load_state(plugin_dir)
        last_prime = state["last_prime"]
        candidate = state["candidate"]

        while not self._is_prime(candidate):
            candidate += 1

        self._append_prime(plugin_dir, candidate)
        commit_message = self.commit_template.format(prime=candidate)
        state["last_prime"] = candidate
        state["candidate"] = candidate + 1  # Fix: update the persisted value based on the found prime
        state["tick"] += 1
        self._save_state(plugin_dir, state)

        return {
            "tick": state["tick"],  # post-increment, matches collatz-explorer's convention
            "prime": candidate,
            "candidate": candidate,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
