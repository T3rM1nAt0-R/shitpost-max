"""Fetches Mars weather data from NASA's InSight lander archive API each tick.

Note: the InSight mission ended in 2022, so this API now serves a frozen
historical archive rather than truly live data -- a known characteristic
of this feed, not a bug.
"""

import json
import urllib.request

from harness.shitpost_base import Shitpost

ENDPOINT = "https://api.nasa.gov/insight_weather/?api_key=DEMO_KEY&feedtype=json&ver=1.0"


def _parse(data):
    sols = data["sol_keys"]
    if not sols:
        raise ValueError("empty sol_keys")
    latest = sols[-1]
    at = data[latest]["AT"]
    return {
        "sol": latest,
        "avg_temp_c": float(at["av"]),
        "min_temp_c": float(at["mn"]),
        "max_temp_c": float(at["mx"]),
        "season": data[latest]["Season"],
    }


class MarsWeatherPlugin(Shitpost):
    """Fetch and emit the most recent available Mars sol's weather. Skips the tick on any fetch failure."""

    name = "mars-weather"
    internal = False
    commit_template = "mars sol {sol}: {avg_temp_c}C avg ({season})"

    def produce(self):
        try:
            with urllib.request.urlopen(ENDPOINT, timeout=15) as response:
                data = json.loads(response.read())
            return _parse(data)
        except Exception:
            return None
