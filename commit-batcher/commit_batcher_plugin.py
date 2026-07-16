"""Generates tiny files every second and batches the commits, because respecting the git log is a choice I make selectively."""

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

    def _log_push(self, plugin_dir: str, commits_since_push: int, total_commits: int) -> None:
        path = os.path.join(plugin_dir, "batcher_log.jsonl")
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
        os.makedirs(os.path.join(plugin_dir, "data"), exist_ok=True)

        state = self._load_persisted_state(default={"tick": 0, "last_push": None})
        tick = state["tick"] + 1
        state["tick"] = tick

        ts = datetime.now(timezone.utc).isoformat()
        random_word = ''.join(random.choices(string.ascii_lowercase, k=5))
        file_path = os.path.join(plugin_dir, f"data/{ts}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(random_word)

        self._save_persisted_state(state)
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
