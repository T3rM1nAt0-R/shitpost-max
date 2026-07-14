import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class CronVsTimerPlugin(Shitpost):
    """Compare cron and systemd timer behavior."""

    name = "cron-vs-timer"
    internal = False
    commit_template = "cron={cron} timer={timer}"

    def __init__(self):
        super().__init__()

    def produce(self) -> dict:
        """Return the current counts and update persistent state."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        default_state = {
            "cron": 0,
            "timer": 0,
        }

        state = self._load_persisted_state(default_state)

        # Increment counters
        state["cron"] += 1
        state["timer"] += 1

        self._save_persisted_state(state)

        return {
            "tick": len(state),
            "cron": state["cron"],
            "timer": state["timer"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
