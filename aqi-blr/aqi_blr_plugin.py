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
        self._state_file_name = "state.jsonl"
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
                    f"warning: aqi-blr state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"timestamp", "aqi", "category", "pm2_5", "pm10", "raw"}
            if not required.issubset(state.keys()):
                print(
                    "warning: aqi-blr state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

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

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _save_summary(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._summary_file_name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)

    def produce(self) -> dict:
        """Fetch and log the current AQI for Bangalore."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

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

        self._save_state(plugin_dir, state)
        self._save_summary(plugin_dir, state)

        return {
            "timestamp": state["timestamp"],
            "aqi": aqi,
            "category": category,
            "pm2_5": pm2_5,
            "pm10": pm10,
        }
