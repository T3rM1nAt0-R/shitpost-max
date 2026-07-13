import os
from datetime import datetime, timezone

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
        url = f"https://api.github.com/search/repositories?q=created:>2023-04-01&sort=stars&order=desc"
        if language:
            url += f"&q=language:{language}"
        headers = {
            "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
            "Accept": "application/vnd.github.v3+json",
        }
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
