import json
import os
import sys
from datetime import datetime, timezone
import requests

from harness.shitpost_base import Shitpost


class EarthquakeLogPlugin(Shitpost):
    """Fetch recent earthquakes from the USGS GeoJSON feed and log details."""

    name = "earthquake-log"
    internal = False
    commit_template = "earthquake-log: {count} quakes, max M{max_magnitude}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "earthquake_log_state.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: earthquake log state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"count", "max_magnitude", "top_event"}
            if not required.issubset(state.keys()):
                print(
                    "warning: earthquake log state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "count": 0,
            "max_magnitude": 0.0,
            "top_event": None,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def produce(self) -> dict:
        """Fetch earthquakes and update state."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        feed_url = os.getenv("FEED_URL", "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson")
        response = requests.get(feed_url)
        if response.status_code != 200:
            print(f"error: failed to fetch earthquake data ({response.status_code})", file=sys.stderr)
            return None

        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            print(f"error: invalid JSON from USGS feed ({exc})", file=sys.stderr)
            return None

        count = len(data["features"])
        max_magnitude = 0.0
        top_event = None

        for feature in data["features"]:
            properties = feature["properties"]
            magnitude = properties.get("mag", 0.0)
            place = properties.get("place")
            time = properties.get("time")
            coordinates = feature["geometry"]["coordinates"]

            if magnitude > max_magnitude:
                max_magnitude = magnitude
                top_event = {
                    "mag": magnitude,
                    "place": place,
                    "time": time,
                    "coordinates": coordinates,
                }

        state["count"] += count
        state["max_magnitude"] = max_magnitude
        state["top_event"] = top_event

        self._save_state(plugin_dir, state)

        return {
            "tick": datetime.now(timezone.utc).isoformat(),
            "count": count,
            "max_magnitude": max_magnitude,
            "top_event": top_event,
        }
