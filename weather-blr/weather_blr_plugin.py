import json
import os
import sys
from datetime import datetime, timezone
import requests

from harness.shitpost_base import Shitpost


class WeatherBlrPlugin(Shitpost):
    """Fetch current weather for Bangalore and log it."""

    name = "weather-blr"
    internal = False
    commit_template = "weather-blr: {temperature_c}°C, {conditions}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "weather_blr_state.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running weather state."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: weather-blr state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"timestamp", "temperature_c", "conditions", "humidity"}
            if not required.issubset(state.keys()):
                print(
                    "warning: weather-blr state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "timestamp": None,
            "temperature_c": None,
            "conditions": None,
            "humidity": None,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def produce(self) -> dict:
        """Fetch weather and update persistent state."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Fetch current weather from Open-Meteo API
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast?latitude=12.97&longitude=77.59&current_weather=true"
        )
        if response.status_code != 200:
            print(f"error: failed to fetch weather ({response.status_code})", file=sys.stderr)
            return None

        data = response.json()
        current_weather = data["current_weather"]
        temperature_c = current_weather["temperature"]
        conditions = self._map_conditions(current_weather["weathercode"])
        humidity = data.get("daily", {}).get("humidity_2m")[0]

        state["timestamp"] = datetime.now(timezone.utc).isoformat()
        state["temperature_c"] = temperature_c
        state["conditions"] = conditions
        state["humidity"] = humidity

        self._save_state(plugin_dir, state)

        return {
            "tick": len(state),
            "timestamp": state["timestamp"],
            "temperature_c": temperature_c,
            "conditions": conditions,
            "humidity": humidity,
        }

    def _map_conditions(self, weathercode: int) -> str:
        """Map weather code to a short conditions string."""
        conditions_map = {
            0: "Clear",
            1: "Fair",
            2: "Partly cloudy",
            3: "Cloudy",
            45: "Mist",
            48: "Fog",
            51: "Drizzle",
            53: "Light drizzle",
            55: "Moderate drizzle",
            57: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            67: "Very heavy rain",
            70: "Light freezing rain",
            72: "Moderate freezing rain",
            75: "Heavy freezing rain",
            77: "Thunderstorm with slight rain",
            80: "Thunderstorm with rain",
            82: "Thunderstorm with heavy rain",
            85: "Ice pellets",
            86: "Hail",
            95: "Slight thunderstorm",
            96: "Moderate thunderstorm",
            99: "Heavy thunderstorm",
        }
        return conditions_map.get(weathercode, "Unknown")
