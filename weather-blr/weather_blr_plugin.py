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

    def produce(self) -> dict:
        """Fetch weather and update persistent state."""
        os.makedirs(self._plugin_dir(), exist_ok=True)

        state = self._load_persisted_state({
            "timestamp": None,
            "temperature_c": None,
            "conditions": None,
            "humidity": None,
        })

        # Fetch current weather from Open-Meteo API (using modern current=
        # parameter syntax which supports relative_humidity_2m, unlike the
        # deprecated current_weather=true which only returned a fixed subset)
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast?"
            "latitude=12.97&longitude=77.59&current=temperature_2m,relative_humidity_2m,weather_code"
        )
        if response.status_code != 200:
            print(f"error: failed to fetch weather ({response.status_code})", file=sys.stderr)
            return None

        data = response.json()
        current = data["current"]
        temperature_c = current["temperature_2m"]
        conditions = self._map_conditions(current["weather_code"])
        humidity = current["relative_humidity_2m"]

        state["timestamp"] = datetime.now(timezone.utc).isoformat()
        state["temperature_c"] = temperature_c
        state["conditions"] = conditions
        state["humidity"] = humidity

        self._save_persisted_state(state)

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
