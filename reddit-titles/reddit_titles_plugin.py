import json
import os
import sys
from datetime import datetime, timezone
import requests

from harness.shitpost_base import Shitpost


class RedditTitlesPlugin(Shitpost):
    """Hourly snapshot of hot post titles from a chosen subreddit."""

    name = "reddit-titles"
    internal = False
    commit_template = "reddit-titles: r/{subreddit} top: {top_title}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "reddit_titles_state.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running Reddit Titles state."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: reddit titles state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"subreddit", "titles", "timestamp"}
            if not required.issubset(state.keys()):
                print(
                    "warning: reddit titles state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "subreddit": os.getenv("SUBREDDIT", "programming"),
            "titles": [],
            "timestamp": None,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def produce(self) -> dict:
        """Return the current hot post titles and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Fetch hot posts from Reddit
        headers = {
            "User-Agent": os.getenv("USER_AGENT", "shitpost-max/reddit-titles")
        }
        response = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=(os.getenv("REDDIT_CLIENT_ID"), os.getenv("REDDIT_CLIENT_SECRET")),
            data={"grant_type": "client_credentials"},
            headers=headers,
        )
        if response.status_code != 200:
            print(f"error: failed to get access token ({response.status_code})")
            return None

        access_token = response.json().get("access_token")
        if not access_token:
            print("error: no access token in response")
            return None

        response = requests.get(
            f"https://oauth.reddit.com/r/{state['subreddit']}/hot?limit=25",
            headers={"Authorization": f"Bearer {access_token}", **headers},
        )
        if response.status_code != 200:
            print(f"error: failed to fetch hot posts ({response.status_code})")
            return None

        data = response.json().get("data", {})
        posts = data.get("children", [])

        titles = [post["data"]["title"] for post in posts]
        if not titles:
            print("warning: no titles fetched")
            return None

        state["titles"] = titles
        state["timestamp"] = datetime.now(timezone.utc).isoformat()

        self._save_state(plugin_dir, state)

        return {
            "subreddit": state["subreddit"],
            "titles": state["titles"],
            "count": len(state["titles"]),
            "top_title": state["titles"][0],
            "timestamp": state["timestamp"]
        }
