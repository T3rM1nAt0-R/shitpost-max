import json
import os
import random
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class CrashServicePlugin(Shitpost):
    """Simulate a service that crashes at random intervals."""

    name = "crash-service"
    internal = False
    commit_template = "selfheal: cycle {n} crashed after {secs}s"

    def __init__(self):
        super().__init__()
        self._state_file_name = "crash_state.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it at cycle 0."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: crash state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"n", "last_crash"}
            if not required.issubset(state.keys()):
                print(
                    "warning: crash state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "n": 0,
            "last_crash": None,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def produce(self) -> dict:
        """Simulate a crash and update persistent state."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Simulate a random sleep interval before crashing
        min_sleep = int(os.getenv("MIN_SLEEP", 5))
        max_sleep = int(os.getenv("MAX_SLEEP", 60))
        sleep_time = random.uniform(min_sleep, max_sleep)
        time.sleep(sleep_time)

        # Crash the service by exiting with code 1
        state["n"] += 1
        state["last_crash"] = datetime.now(timezone.utc).isoformat()
        self._save_state(plugin_dir, state)

        return {
            "tick": state["n"],
            "secs": sleep_time,
            "timestamp": state["last_crash"],
        }
