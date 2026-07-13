import json
import os
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from harness.shitpost_base import Shitpost


class StandupPlugin(Shitpost):
    """Generate daily standup updates."""

    name = "agile-theater"
    internal = False
    commit_template = "standup: {date}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "standups_state.json"
        self._standups_file_name = "standups.txt"

    def _load_state(self, plugin_dir: str) -> Dict[str, Optional[Dict[str, str]]]:
        """Load the running standup state."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: standup state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return {}
            # Guard against manual tampering / old versions.
            required = {"last_date"}
            if not required.issubset(state.keys()):
                print(
                    "warning: standup state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return {}
            return state

        return {}

    def _save_state(self, plugin_dir: str, state: Dict[str, Optional[Dict[str, str]]]) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _append_standup(self, plugin_dir: str, standup: str) -> None:
        path = os.path.join(plugin_dir, self._standups_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(standup + "\n")

    def produce(self) -> Optional[Dict[str, str]]:
        """Generate and return a standup block."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        today = datetime.now(timezone.utc).date()

        if "last_date" in state and state["last_date"] == str(today):
            return None

        yesterday = today - timedelta(days=1)
        standup_block = f"# {today}\n\nYesterday:\n- Placeholder for what was done.\n\nToday:\n- Placeholder for what will be done.\n\nBlockers:\n- Placeholder for blockers.\n"

        self._save_state(plugin_dir, {"last_date": str(today)})
        self._append_standup(plugin_dir, standup_block)

        return {
            "date": today.isoformat(),
            "standup": standup_block,
        }
