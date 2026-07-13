import json
import os
import sys
from datetime import datetime, timezone
import requests

from harness.shitpost_base import Shitpost


class IssTracker(Shitpost):
    """Track the International Space Station's latitude and longitude every minute."""

    name = "iss-tracker"
    internal = False
    commit_template = "iss-tracker: lat {latitude}, lon {longitude}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "iss_tracker_state.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running ISS tracker state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: iss-tracker state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"latitude", "longitude", "timestamp"}
            if not required.issubset(state.keys()):
                print(
                    "warning: iss-tracker state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "latitude": None,
            "longitude": None,
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
        """Fetch the current ISS position and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        try:
            response = requests.get("http://api.open-notify.org/iss-now.json")
            response.raise_for_status()
            data = response.json()
            latitude = float(data["iss_position"]["latitude"])
            longitude = float(data["iss_position"]["longitude"])
            api_timestamp = datetime.fromisoformat(data["timestamp"]).astimezone(timezone.utc).isoformat()
        except (requests.RequestException, KeyError, ValueError) as exc:
            print(f"error: failed to fetch ISS position ({exc})", file=sys.stderr)
            return None

        state["latitude"] = latitude
        state["longitude"] = longitude
        state["timestamp"] = api_timestamp

        self._save_state(plugin_dir, state)

        return {
            "latitude": latitude,
            "longitude": longitude,
            "api_timestamp": api_timestamp,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
