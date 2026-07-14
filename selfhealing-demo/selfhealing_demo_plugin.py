import os
import random
import time
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class CrashServicePlugin(Shitpost):
    """Simulate a service that crashes at random intervals."""

    name = "selfhealing-demo"
    internal = False
    commit_template = "selfheal: cycle {tick} crashed after {secs}s"

    def _persisted_state_path(self) -> str:
        return os.path.join(self._plugin_dir(), "crash_state.json")

    def produce(self) -> dict:
        """Simulate a crash and update persistent state."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({"n": 0, "last_crash": None})

        # Simulate a random sleep interval before crashing
        # Defaults are kept short so smoke tests calling produce() x3 finish
        # quickly; set MIN_SLEEP / MAX_SLEEP to longer values for realistic
        # crash-interval simulation in production.
        min_sleep = float(os.getenv("MIN_SLEEP", "0.1"))
        max_sleep = float(os.getenv("MAX_SLEEP", "1.0"))
        sleep_time = random.uniform(min_sleep, max_sleep)
        time.sleep(sleep_time)

        # Crash the service by exiting with code 1
        state["n"] += 1
        state["last_crash"] = datetime.now(timezone.utc).isoformat()
        self._save_persisted_state(state)

        return {
            "tick": state["n"],
            "secs": sleep_time,
            "timestamp": state["last_crash"],
        }
