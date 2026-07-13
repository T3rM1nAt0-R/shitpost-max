import json
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
        self._state_file_name = "thought_leader_state.json"
        self._platitudes_file_name = "platitudes.txt"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it at day 0."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: thought leader state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"last_tick", "tick"}
            if not required.issubset(state.keys()):
                print(
                    "warning: thought leader state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "last_tick": None,
            "tick": 0,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _append_platitude(self, plugin_dir: str, platitude: str) -> None:
        path = os.path.join(plugin_dir, self._platitudes_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(platitude + "\n")

    def produce(self) -> dict:
        """Return the next LinkedIn-style platitude and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

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

        self._save_state(plugin_dir, state)
        self._append_platitude(plugin_dir, f"{platitude} — {today.isoformat()}")

        return {
            "tick": state["tick"],
            "platitude": platitude,
            "timestamp": today.isoformat(),
        }
