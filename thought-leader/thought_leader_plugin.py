"""Generates one LinkedIn-style platitude daily, indistinguishable from 90% of my actual feed."""

import os
import random
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class ThoughtLeaderPlugin(Shitpost):
    """Generate one LinkedIn-style platitude per day."""

    name = "thought-leader"
    internal = False
    commit_template = "thought: {platitude}"

    def __init__(self):
        super().__init__()
        self._platitudes_file_name = "platitudes.txt"

    def _append_platitude(self, plugin_dir: str, platitude: str) -> None:
        path = os.path.join(plugin_dir, self._platitudes_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(platitude + "\n")

    def produce(self) -> dict:
        """Return the next LinkedIn-style platitude and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({"last_tick": None, "tick": 0})

        today = datetime.now(timezone.utc).date()

        if state["last_tick"] == str(today):
            return None

        buzzwords = ["innovation", "growth", "strategy", "vision", "execution"]
        calls_to_action = ["act now", "take action", "join us", "learn more"]

        template = "{buzzword} is key to {call_to_action}."
        platitude = template.format(
            buzzword=random.choice(buzzwords),
            call_to_action=random.choice(calls_to_action)
        )

        state["last_tick"] = str(today)
        state["tick"] += 1

        self._save_persisted_state(state)
        self._append_platitude(plugin_dir, f"{platitude} — {today.isoformat()}")

        return {
            "tick": state["tick"],
            "platitude": platitude,
            "timestamp": today.isoformat(),
        }
