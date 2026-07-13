import json
import os
import sys
from datetime import datetime, timezone
from urllib.request import urlopen

from harness.shitpost_base import Shitpost


class WikipediaFeatured(Shitpost):
    """Daily log of Wikipedia's featured article (English), logged to JSONL."""

    name = "wikipedia-featured"
    internal = False
    commit_template = "wikipedia-featured: {title}"

    def produce(self) -> dict | None:
        """Fetch today's featured article from the Wikimedia feed API and update state."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({"timestamp": None, "title": "", "extract": "", "url": ""})
        today = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        url = f"https://api.wikimedia.org/feed/v1/wikipedia/en/featured/{today}"

        try:
            with urlopen(url) as response:
                data = json.loads(response.read().decode("utf-8"))
                tfa = data.get("tfa", {})
                title = tfa.get("title", "")
                extract = tfa.get("extract", "")
                url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
        except Exception as e:
            print(f"error: failed to fetch featured article ({e})", file=sys.stderr)
            return None

        if not title or not url:
            print("warning: fetched empty title or URL", file=sys.stderr)
            return None

        state["timestamp"] = datetime.now(timezone.utc).isoformat()
        state["title"] = title
        state["extract"] = extract
        state["url"] = url

        self._save_persisted_state(state)

        return {
            "timestamp": state["timestamp"],
            "title": state["title"],
            "extract": state["extract"],
            "url": state["url"]
        }
