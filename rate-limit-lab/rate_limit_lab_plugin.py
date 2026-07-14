import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class RateLimitLabPlugin(Shitpost):
    """Simulate a rate-limited endpoint and compare aggressive vs compliant clients."""

    name = "rate-limit-lab"
    internal = False
    commit_template = "ratelimit: aggressive={aggressive_429s}/{aggressive_total} compliant={compliant_429s}/{compliant_total}"

    def _persisted_state_path(self) -> str:
        """Preserve legacy filename so existing persisted state is not lost."""
        return os.path.join(self._plugin_dir(), "rate_limit_state.json")

    def produce(self) -> dict:
        """Simulate a rate-limited endpoint and compare clients."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "aggressive_429s": 0,
            "aggressive_total": 0,
            "compliant_429s": 0,
            "compliant_total": 0,
        })

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

        self._save_persisted_state(state)

        return {
            "tick": len(state),
            "aggressive_429s": aggressive_429s,
            "aggressive_total": state["aggressive_total"],
            "compliant_429s": compliant_429s,
            "compliant_total": state["compliant_total"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
