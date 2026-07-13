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
        self._summary_file_name = "summary.json"

    def _fetch_downloads(self) -> int:
        state = self._load_persisted_state({
            "package": os.getenv("PACKAGE", "lodash"),
            "period": os.getenv("PERIOD", "last-week"),
            "downloads": 0,
        })
        package = state["package"]
        period = state["period"]
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

        state = self._load_persisted_state({
            "package": os.getenv("PACKAGE", "lodash"),
            "period": os.getenv("PERIOD", "last-week"),
            "downloads": 0,
        })

        # Fetch the latest downloads
        downloads = self._fetch_downloads()

        # Update the state
        state["downloads"] += downloads

        self._save_persisted_state(state)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "package": state["package"],
            "period": state["period"],
            "downloads": state["downloads"],
        }
