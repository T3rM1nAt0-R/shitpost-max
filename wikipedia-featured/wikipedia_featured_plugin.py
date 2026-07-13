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

    def __init__(self):
        super().__init__()
        self._state_file_name = "wikipedia_featured_state.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: wikipedia featured state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"timestamp", "title", "extract", "url"}
            if not required.issubset(state.keys()):
                print(
                    "warning: wikipedia featured state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "timestamp": None,
            "title": "",
            "extract": "",
            "url": ""
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def produce(self) -> dict | None:
        """Fetch today's featured article from the Wikimedia feed API and update state."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
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

        self._save_state(plugin_dir, state)

        return {
            "timestamp": state["timestamp"],
            "title": state["title"],
            "extract": state["extract"],
            "url": state["url"]
        }
