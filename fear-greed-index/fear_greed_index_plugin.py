"""Logs the market fear/greed index daily so I can watch collective emotion get a number."""

import json
import os
import sys
import requests
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class FearGreedIndexPlugin(Shitpost):
    """Fetch and record daily fear/greed index."""

    name = "fear-greed-index"
    internal = False
    commit_template = "fear-greed: {score} ({classification})"

    def __init__(self):
        super().__init__()
        self._state_file_name = "state.jsonl"
        self._chart_file_name = "chart.svg"

    def _load_state(self, plugin_dir: str) -> list:
        """Load the running state, or initialise it as an empty list."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = [json.loads(line) for line in f]
            except json.JSONDecodeError as exc:
                print(
                    f"warning: state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return []
        else:
            state = []

        return state

    def _save_state(self, plugin_dir: str, state: list) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            for entry in state:
                json.dump(entry, f)
                f.write("\n")
        os.replace(tmp_path, path)

    def _fetch_fear_greed_index(self) -> dict:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Referer": "https://edition.cnn.com/markets/fear-and-greed",
        }
        # Real bug, found 2026-07-17: urllib.request got a 418 from this
        # endpoint with these exact headers every single time (confirmed
        # live), while `requests` with the identical headers gets a clean
        # 200 -- CNN's edge is fingerprinting the HTTP client itself, not
        # just headers. This plugin had never produced a tick as a result.
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "score": data["fear_and_greed"]["score"],
                "classification": data["fear_and_greed"]["rating"]
            }
        else:
            raise Exception(f"Failed to fetch fear/greed index: {response.status_code}")

    def produce(self) -> dict:
        """Fetch the daily fear/greed index and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        try:
            fear_greed_index = self._fetch_fear_greed_index()
        except Exception as exc:
            print(f"warning: failed to fetch fear/greed index ({exc}); skipping tick", file=sys.stderr)
            return None

        timestamp = datetime.now(timezone.utc).isoformat()
        entry = {
            "timestamp": timestamp,
            **fear_greed_index
        }
        state.append(entry)

        self._save_state(plugin_dir, state)

        return {
            "tick": len(state),
            "score": fear_greed_index["score"],
            "classification": fear_greed_index["classification"],
            "timestamp": timestamp
        }
