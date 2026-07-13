import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class AqiBlrPlugin(Shitpost):
    """Fetch and log Bangalore air-quality index snapshot hourly."""

    name = "aqi-blr"
    internal = False
    commit_template = "aqi-blr: AQI {aqi} ({category})"

    def __init__(self):
        super().__init__()

    @staticmethod
    def _default_state() -> dict:
        return {
            "timestamp": None,
            "aqi": None,
            "category": None,
            "pm2_5": None,
            "pm10": None,
            "raw": None,
        }

    def produce(self) -> dict:
        """Fetch and log the current AQI for Bangalore."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state(self._default_state())

        # Fetch current AQI data from Open-Meteo API
        url = "https://air-quality-api.open-meteo.com/v1/air-quality?latitude=12.97&longitude=77.59&current=us_aqi,pm10,pm2_5"
        response = urllib.request.urlopen(url)
        if response.status != 200:
            print(f"error: failed to fetch AQI data ({response.status})", file=sys.stderr)
            return None

        data = json.loads(response.read().decode("utf-8"))
        current = data["current"]
        aqi = current["us_aqi"]
        pm10 = current["pm10"]
        pm2_5 = current["pm2_5"]

        # Map AQI to category
        if aqi <= 50:
            category = "Good"
        elif aqi <= 100:
            category = "Moderate"
        elif aqi <= 150:
            category = "Unhealthy for Sensitive Groups"
        elif aqi <= 200:
            category = "Unhealthy"
        elif aqi <= 300:
            category = "Very Unhealthy"
        else:
            category = "Hazardous"

        # Update state
        state["timestamp"] = datetime.now(timezone.utc).isoformat()
        state["aqi"] = aqi
        state["category"] = category
        state["pm2_5"] = pm2_5
        state["pm10"] = pm10
        state["raw"] = data

        self._save_persisted_state(state)

        return {
            "timestamp": state["timestamp"],
            "aqi": aqi,
            "category": category,
            "pm2_5": pm2_5,
            "pm10": pm10,
        }
