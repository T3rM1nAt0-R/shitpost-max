import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost
import requests

class EmojiSummaryPlugin(Shitpost):
    """Summarise a day's top text into exactly 3 emojis using a local model."""

    name = "emoji-summary"
    internal = False
    commit_template = "emoji-summary: {emoji_output}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "emoji_summary_state.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running emoji summary state."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: emoji summary state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"tick", "source_text", "emoji_output", "emoji_count", "accepted", "timestamp"}
            if not required.issubset(state.keys()):
                print(
                    "warning: emoji summary state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "tick": 0,
            "source_text": "",
            "emoji_output": "",
            "emoji_count": 0,
            "accepted": False,
            "timestamp": ""
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _fetch_source_text(self) -> str:
        """Fetch the top Hacker News story title + URL via the Firebase API."""
        try:
            response = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json")
            response.raise_for_status()
            top_stories = response.json()
            if not top_stories:
                return "No stories found on Hacker News"
            story_id = top_stories[0]
            story_response = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
            story_response.raise_for_status()
            story = story_response.json()
            return f"{story['title']} - {story['url']}"
        except requests.RequestException as exc:
            print(
                f"warning: failed to fetch Hacker News story ({exc}); falling back to random note",
                file=sys.stderr,
            )
            return "Random note"

    def _call_ollama(self, text: str) -> str:
        """Send the source text to Ollama and get the emoji summary."""
        # Placeholder for actual Ollama call
        return "😊😢😔"  # Example output

    def produce(self) -> dict:
        """Return the emoji summary and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        source_text = self._fetch_source_text()

        emoji_output = self._call_ollama(source_text)
        emoji_count = len(emoji_output.strip())

        if emoji_count != 3:
            print(
                f"warning: emoji output is not exactly 3 emojis ({emoji_count}), retrying",
                file=sys.stderr,
            )
            return None

        state["tick"] += 1
        state["source_text"] = source_text
        state["emoji_output"] = emoji_output
        state["emoji_count"] = emoji_count
        state["accepted"] = True
        state["timestamp"] = datetime.now(timezone.utc).isoformat()

        self._save_state(plugin_dir, state)

        return {
            "tick": state["tick"],
            "source_text": source_text,
            "emoji_output": emoji_output,
            "emoji_count": emoji_count,
            "accepted": True,
            "timestamp": state["timestamp"]
        }
