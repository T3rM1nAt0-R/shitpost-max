import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class HaikuDailyPlugin(Shitpost):
    """Generate one syllable-counted haiku each day using a local LLM and append it to a growing collection."""

    name = "haiku-daily"
    internal = False
    commit_template = "haiku: {s1} / {s2} / {s3}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "haiku_state.jsonl"
        self._haiku_file_name = "haiku.txt"

    def _load_state(self, plugin_dir: str) -> list:
        """Load the running haiku state, or initialise it as an empty list."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = [json.loads(line) for line in f]
            except json.JSONDecodeError as exc:
                print(
                    f"warning: haiku state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return []
        else:
            state = []

        return state

    def _save_state(self, plugin_dir: str, state: list) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        with open(path, "w", encoding="utf-8") as f:
            for entry in state:
                json.dump(entry, f)
                f.write("\n")

    def _append_haiku(self, plugin_dir: str, haiku: list) -> None:
        path = os.path.join(plugin_dir, self._haiku_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"---\n{datetime.now(timezone.utc).isoformat()}\n")
            for line in haiku:
                f.write(line + "\n")

    def produce(self) -> dict:
        """Return the next haiku and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Query local model for a haiku
        haiku = self._query_model()

        if not self._validate_haiku(haiku):
            return None

        state.append({
            "tick": len(state) + 1,
            "lines": haiku,
            "syllable_counts": [len(line.split()) for line in haiku],
            "accepted": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        self._save_state(plugin_dir, state)
        self._append_haiku(plugin_dir, haiku)

        return {
            "tick": len(state),
            "lines": haiku,
            "syllable_counts": [len(line.split()) for line in haiku],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _query_model(self) -> list:
        # Placeholder for querying local model
        return ["This is a", "sample haiku.", "With 5-7-5 syllables."]

    def _validate_haiku(self, haiku: list) -> bool:
        if len(haiku) != 3:
            return False

        syllable_counts = [len(line.split()) for line in haiku]
        if not (5 <= syllable_counts[0] <= 7 and 5 <= syllable_counts[2] <= 7):
            return False

        return True
