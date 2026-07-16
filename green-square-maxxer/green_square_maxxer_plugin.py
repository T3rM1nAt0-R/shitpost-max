"""Commits exactly once per calendar day to keep the GitHub contribution graph green. Engineering discipline, or an addiction — undecided."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class GreenSquareMaxxerPlugin(Shitpost):
    """Commit exactly once per calendar day."""

    name = "green-square-maxxer"
    internal = False
    commit_template = "green square {date}"

    def __init__(self):
        super().__init__()

    def produce(self) -> dict | None:
        """Return the next commit if today has no commit yet."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state(default={"last_commit_date": None, "tick": 0})
        today = datetime.now(timezone.utc).date().isoformat()

        # Check if today already has a commit
        if state["last_commit_date"] == today:
            return None

        # Append today's date to green-squares.txt and update state
        with open(os.path.join(plugin_dir, "green-squares.txt"), "a", encoding="utf-8") as f:
            f.write(today + "\n")

        state["last_commit_date"] = today
        state["tick"] += 1

        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "date": today,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
