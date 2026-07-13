import os
from datetime import datetime, timezone
import requests

from harness.shitpost_base import Shitpost


class RedditTitlesPlugin(Shitpost):
    """Hourly snapshot of hot post titles from a chosen subreddit."""

    name = "reddit-titles"
    internal = False
    commit_template = "reddit-titles: r/{subreddit} top: {top_title}"

    def produce(self) -> dict:
        """Return the current hot post titles and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "subreddit": os.getenv("SUBREDDIT", "programming"),
            "titles": [],
            "timestamp": None,
        })

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

        self._save_persisted_state(state)

        return {
            "subreddit": state["subreddit"],
            "titles": state["titles"],
            "count": len(state["titles"]),
            "top_title": state["titles"][0],
            "timestamp": state["timestamp"]
        }
