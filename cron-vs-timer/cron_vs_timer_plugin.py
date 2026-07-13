import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class CronVsTimerPlugin(Shitpost):
    """Compare cron and systemd timer behavior."""

    name = "cron-vs-timer"
    internal = False
    commit_template = "cron={c} timer={t} diff={d}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "cron_vs_timer_state.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: cron_vs_timer state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"cron", "timer"}
            if not required.issubset(state.keys()):
                print(
                    "warning: cron_vs_timer state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "cron": 0,
            "timer": 0,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def produce(self) -> dict:
        """Return the current counts and update persistent state."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Increment counters
        state["cron"] += 1
        state["timer"] += 1

        self._save_state(plugin_dir, state)

        return {
            "tick": len(state),
            "cron": state["cron"],
            "timer": state["timer"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
