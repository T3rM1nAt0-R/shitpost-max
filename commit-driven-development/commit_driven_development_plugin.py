import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class CommitDrivenDevelopmentPlugin(Shitpost):
    """Increment an integer on every tick."""

    name = "commit-driven-development"
    internal = False
    commit_template = "commit count: {count}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "commits.txt"

    def _load_state(self, plugin_dir: str) -> int:
        """Load the running state, or initialise it at 0."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    count = int(f.read().strip())
            except ValueError as exc:
                print(
                    f"warning: commits state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return 0
        else:
            count = 0

        return count

    def _save_state(self, plugin_dir: str, count: int) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(count))

    def produce(self) -> dict:
        """Return the next commit count and update persistent file."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        current_count = self._load_state(plugin_dir)
        new_count = current_count + 1

        self._save_state(plugin_dir, new_count)

        return {
            "tick": new_count,
            "count": new_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
