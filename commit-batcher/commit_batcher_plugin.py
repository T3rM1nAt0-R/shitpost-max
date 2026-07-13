import json
import os
import random
import string
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class CommitBatcherPlugin(Shitpost):
    """Generate a small new file every second and batch commits."""

    name = "commit-batcher"
    internal = False
    commit_template = "data: snapshot {ts}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "batcher_state.json"
        self._log_file_name = "batcher_log.jsonl"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it at tick 0."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: commit-batcher state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"tick", "last_push"}
            if not required.issubset(state.keys()):
                print(
                    "warning: commit-batcher state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "tick": 0,
            "last_push": None,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _log_push(self, plugin_dir: str, commits_since_push: int, total_commits: int) -> None:
        path = os.path.join(plugin_dir, self._log_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": datetime.now(timezone.utc).isoformat(),
                "commits_since_push": commits_since_push,
                "total_commits": total_commits,
            }) + "\n")

    def produce(self) -> dict | None:
        """Create a new file and commit it every second."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        tick = state["tick"] + 1
        state["tick"] = tick

        ts = datetime.now(timezone.utc).isoformat()
        random_word = ''.join(random.choices(string.ascii_lowercase, k=5))
        file_path = os.path.join(plugin_dir, f"data/{ts}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(random_word)

        self._save_state(plugin_dir, state)
        print(f"tick {tick}: created data/{ts}.txt with word '{random_word}'")

        if tick % 600 == 0:
            commits_since_push = 600
            total_commits = tick
            self._log_push(plugin_dir, commits_since_push, total_commits)
            print(f"pushing {commits_since_push} commits to remote")
            # Simulate git push here (not implemented for this example)

        return {
            "tick": tick,
            "ts": ts,
            "random_word": random_word,
        }
