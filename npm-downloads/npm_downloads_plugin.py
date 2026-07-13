import json
import os
import sys
from datetime import datetime, timezone
import requests

from harness.shitpost_base import Shitpost


class NpmDownloadsPlugin(Shitpost):
    """Daily download count for a chosen npm package."""

    name = "npm-downloads"
    internal = False
    commit_template = "npm-downloads: {package} {downloads} downloads in {period}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "npm_downloads_state.json"
        self._summary_file_name = "summary.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: npm-downloads state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"package", "period", "downloads"}
            if not required.issubset(state.keys()):
                print(
                    "warning: npm-downloads state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "package": os.getenv("PACKAGE", "lodash"),
            "period": os.getenv("PERIOD", "last-week"),
            "downloads": 0,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _fetch_downloads(self) -> int:
        package = self._load_state(self._plugin_dir())["package"]
        period = self._load_state(self._plugin_dir())["period"]
        url = f"https://api.npmjs.org/downloads/point/{period}/{package}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get("downloads", 0)
        else:
            print(f"warning: failed to fetch npm downloads for {package} ({response.status_code})", file=sys.stderr)
            return 0

    def produce(self) -> dict:
        """Return the download count and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Fetch the latest downloads
        downloads = self._fetch_downloads()

        # Update the state
        state["downloads"] += downloads

        self._save_state(plugin_dir, state)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "package": state["package"],
            "period": state["period"],
            "downloads": state["downloads"],
        }
