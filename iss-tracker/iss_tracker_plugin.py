import os
from datetime import datetime, timezone
import requests

from harness.shitpost_base import Shitpost


class IssTracker(Shitpost):
    """Track the International Space Station's latitude and longitude every minute."""

    name = "iss-tracker"
    internal = False
    commit_template = "iss-tracker: lat {latitude}, lon {longitude}"

    def produce(self) -> dict:
        """Fetch the current ISS position and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "latitude": None,
            "longitude": None,
            "timestamp": None,
        })

        try:
            response = requests.get("http://api.open-notify.org/iss-now.json")
            response.raise_for_status()
            data = response.json()
            latitude = float(data["iss_position"]["latitude"])
            longitude = float(data["iss_position"]["longitude"])
            api_timestamp = datetime.fromtimestamp(int(data["timestamp"]), tz=timezone.utc).isoformat()
        except (requests.RequestException, KeyError, ValueError) as exc:
            print(f"error: failed to fetch ISS position ({exc})", file=sys.stderr)
            return None

        state["latitude"] = latitude
        state["longitude"] = longitude
        state["timestamp"] = api_timestamp

        self._save_persisted_state(state)

        return {
            "latitude": latitude,
            "longitude": longitude,
            "api_timestamp": api_timestamp,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
