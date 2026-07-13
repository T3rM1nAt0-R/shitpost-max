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
        self._state_file_name = "green_squares_state.json"
        self._dates_file_name = "green-squares.txt"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it at today's date."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: green square state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"last_commit_date", "tick"}
            if not required.issubset(state.keys()):
                print(
                    "warning: green square state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "last_commit_date": None,
            "tick": 0,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def produce(self) -> dict | None:
        """Return the next commit if today has no commit yet."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        today = datetime.now(timezone.utc).date().isoformat()

        # Check if today already has a commit
        if state["last_commit_date"] == today:
            return None

        # Append today's date to green-squares.txt and update state
        with open(os.path.join(plugin_dir, self._dates_file_name), "a", encoding="utf-8") as f:
            f.write(today + "\n")

        state["last_commit_date"] = today
        state["tick"] += 1

        self._save_state(plugin_dir, state)

        return {
            "tick": state["tick"],
            "date": today,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
