import json
import os
import sys
from datetime import datetime, timezone
import requests

from harness.shitpost_base import Shitpost


class HnFrontpagePlugin(Shitpost):
    """Hourly snapshot of Hacker News front-page titles."""

    name = "hn-frontpage"
    internal = False
    commit_template = "hn-frontpage: {count} stories, top: {top_title}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "hn_frontpage_state.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: hn-frontpage state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"stories", "tick"}
            if not required.issubset(state.keys()):
                print(
                    "warning: hn-frontpage state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "stories": [],
            "tick": 0,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def produce(self) -> dict:
        """Return the next snapshot of Hacker News front-page titles."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Fetch top 30 story IDs
        response = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json")
        if response.status_code != 200:
            print(f"Failed to fetch top stories: {response.status_code}", file=sys.stderr)
            return None

        story_ids = response.json()[:30]

        # Resolve each ID to title and URL
        stories = []
        for story_id in story_ids:
            story_response = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
            if story_response.status_code != 200:
                print(f"Failed to fetch story {story_id}: {story_response.status_code}", file=sys.stderr)
                continue

            story_data = story_response.json()
            stories.append({
                "id": story_id,
                "title": story_data.get("title", ""),
                "url": story_data.get("url", "")
            })

        # Append snapshot (timestamp + titles/urls list) to state.jsonl
        timestamp = datetime.now(timezone.utc).isoformat()
        snapshot = {
            "timestamp": timestamp,
            "stories": stories
        }
        state["stories"] += stories
        state["tick"] += 1

        self._save_state(plugin_dir, state)

        return {
            "tick": state["tick"],
            "count": len(stories),
            "top_title": stories[0]["title"] if stories else "",
            "timestamp": timestamp,
        }
