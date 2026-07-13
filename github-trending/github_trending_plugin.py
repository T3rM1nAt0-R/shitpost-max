import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class GithubTrending(Shitpost):
    """Daily snapshot of trending GitHub repositories."""

    name = "github-trending"
    internal = False
    commit_template = "github-trending: {top_repo} ({top_stars} stars today)"

    def __init__(self):
        super().__init__()
        self._state_file_name = "trending_state.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running trending state."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: github-trending state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"tick", "repos"}
            if not required.issubset(state.keys()):
                print(
                    "warning: github-trending state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "tick": 0,
            "repos": [],
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def produce(self) -> dict | None:
        """Fetch trending repositories and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

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

        self._save_state(plugin_dir, state)

        return {
            "tick": state["tick"],
            "language": language,
            "repos": repos,
            "top_repo": top_repo,
            "top_stars": top_stars,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
