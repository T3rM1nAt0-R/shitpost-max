"""Snapshots trending GitHub repos daily so I always know what everyone else shipped instead of this."""

import os
from datetime import datetime, timezone

import requests

from harness.shitpost_base import Shitpost


class GithubTrending(Shitpost):
    """Daily snapshot of trending GitHub repositories."""

    name = "github-trending"
    internal = False
    commit_template = "github-trending: {top_repo} ({top_stars} stars today)"

    def __init__(self):
        super().__init__()

    def _persisted_state_path(self) -> str:
        """Use the original custom filename to avoid silently losing state."""
        return os.path.join(self._plugin_dir(), "trending_state.json")

    def produce(self) -> dict | None:
        """Fetch trending repositories and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({"tick": 0, "repos": []})

        # Fetch trending repositories
        language = os.getenv("LANGUAGE", "")
        # Real bug (DeepSeek review, 2026-07-17): appending a second "&q="
        # parameter doesn't add to the existing search query -- GitHub's
        # API only honors one q= value, so the language filter was silently
        # ignored (or clobbered the date filter, depending on parse order)
        # whenever LANGUAGE was set. GitHub's search syntax combines
        # multiple terms with a space inside the single q= value.
        query = "created:>2023-04-01"
        if language:
            query += f" language:{language}"
        url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc"
        headers = {"Accept": "application/vnd.github.v3+json"}
        # Real bug, found 2026-07-17: this used to always set
        # Authorization: token None when GITHUB_TOKEN wasn't set, instead of
        # omitting the header -- GitHub correctly 401s a literal "token
        # None" credential (confirmed live: identical request with no auth
        # header at all returns 200). GITHUB_TOKEN was never actually
        # configured for this plugin, so it had never produced a tick.
        # Unauthenticated search API calls work fine, just at a lower rate
        # limit (10/min vs 30/min) -- acceptable for a plugin that only
        # ticks once per its own cadence anyway.
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"token {github_token}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"error: failed to fetch trending repositories ({response.status_code})")
            return None

        data = response.json()
        repos = [
            {
                "name": item["full_name"],
                "stars_today": item["stargazers_count"] - state["repos"][i]["stars_today"] if i < len(state["repos"]) else item["stargazers_count"],
                "url": item["html_url"],
            }
            for i, item in enumerate(data["items"])
        ]
        top_repo = repos[0]["name"]
        top_stars = repos[0]["stars_today"]

        state["tick"] += 1
        state["repos"] = repos

        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "language": language,
            "repos": repos,
            "top_repo": top_repo,
            "top_stars": top_stars,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
