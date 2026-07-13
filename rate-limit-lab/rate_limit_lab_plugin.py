import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class RateLimitLabPlugin(Shitpost):
    """Simulate a rate-limited endpoint and compare aggressive vs compliant clients."""

    name = "rate-limit-lab"
    internal = False
    commit_template = "ratelimit: aggressive={a_429s}/{a_total} compliant={c_429s}/{c_total}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "rate_limit_state.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: rate limit state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            required = {"aggressive_429s", "aggressive_total", "compliant_429s", "compliant_total"}
            if not required.issubset(state.keys()):
                print(
                    "warning: rate limit state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "aggressive_429s": 0,
            "aggressive_total": 0,
            "compliant_429s": 0,
            "compliant_total": 0,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def produce(self) -> dict:
        """Simulate a rate-limited endpoint and compare clients."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Simulate aggressive client
        aggressive_429s = 0
        for _ in range(10):
            if state["aggressive_total"] >= 5:
                aggressive_429s += 1
            else:
                state["aggressive_total"] += 1

        # Simulate compliant client
        compliant_429s = 0
        for _ in range(10):
            if state["compliant_total"] >= 5:
                compliant_429s += 1
            else:
                state["compliant_total"] += 1

        state["aggressive_429s"] += aggressive_429s
        state["compliant_429s"] += compliant_429s

        self._save_state(plugin_dir, state)

        return {
            "tick": len(state),
            "aggressive_429s": aggressive_429s,
            "aggressive_total": state["aggressive_total"],
            "compliant_429s": compliant_429s,
            "compliant_total": state["compliant_total"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
