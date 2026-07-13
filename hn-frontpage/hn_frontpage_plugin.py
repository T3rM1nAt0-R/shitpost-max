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

    def produce(self) -> dict:
        """Return the next snapshot of Hacker News front-page titles."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({"stories": [], "tick": 0})

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

        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "count": len(stories),
            "top_title": stories[0]["title"] if stories else "",
            "timestamp": timestamp,
        }
