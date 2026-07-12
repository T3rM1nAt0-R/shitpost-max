import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class TwinPrimesPlugin(Shitpost):
    """Find twin prime pairs."""

    name = "twin-primes"
    internal = False
    commit_template = "candidate {candidate}: {twin}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "twin_primes_state.json"
        self._twins_file_name = "twins.txt"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running twin primes state, or initialise it for the first tick."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: twin primes state file is corrupt ({exc}); starting fresh",
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
                    "warning: twin primes state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        # Start with last_prime=2, candidate=3, and tick=0
        return {
            "last_prime": 2,
            "candidate": 3,
            "tick": 0,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

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

        state = self._load_state(plugin_dir)
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
        self._save_state(plugin_dir, state)

        return {
            "tick": state["tick"],  # post-increment, matches collatz-explorer's convention
            "candidate": candidate,
            "twin": [last_prime, candidate] if commit_message else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        } if commit_message else None
