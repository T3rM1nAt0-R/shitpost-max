import json
import os
import sys
import urllib.error
import urllib.request

from harness.shitpost_base import Shitpost


class EarthquakeLogPlugin(Shitpost):
    """Fetch recent earthquakes from the USGS GeoJSON feed and log details."""

    name = "earthquake-log"
    internal = False
    commit_template = "earthquake-log: {count} quakes, max M{max_magnitude}"

    def __init__(self):
        super().__init__()

    def produce(self) -> dict:
        """Fetch earthquakes and update state."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        default_state = {
            "count": 0,
            "max_magnitude": 0.0,
            "top_event": None,
        }

        state = self._load_persisted_state(default_state)

        feed_url = os.getenv("FEED_URL", "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson")
        try:
            with urllib.request.urlopen(feed_url, timeout=30) as response:
                if response.getcode() != 200:
                    print(
                        f"error: failed to fetch earthquake data ({response.getcode()})",
                        file=sys.stderr,
                    )
                    return None

                try:
                    data = json.loads(response.read().decode("utf-8"))
                except json.JSONDecodeError as exc:
                    print(
                        f"error: invalid JSON from USGS feed ({exc})",
                        file=sys.stderr,
                    )
                    return None
        except urllib.error.HTTPError as exc:
            print(
                f"error: failed to fetch earthquake data ({exc.code})",
                file=sys.stderr,
            )
            return None
        except urllib.error.URLError as exc:
            print(
                f"error: failed to fetch earthquake data ({exc.reason})",
                file=sys.stderr,
            )
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

        self._save_persisted_state(state)

        return {
            "count": count,
            "max_magnitude": max_magnitude,
            "top_event": top_event,
        }
