"""Fetches the current planetary Kp-index from NOAA SWPC's public API each tick."""

import json
import urllib.request

from harness.shitpost_base import Shitpost

ENDPOINT = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"


def _parse(readings):
    if not readings:
        raise ValueError("empty readings list")
    latest = readings[-1]
    kp = float(latest["Kp"])
    if kp > 6:
        likelihood = "likely at mid latitudes"
    elif kp >= 4:
        likelihood = "possible at high latitudes"
    else:
        likelihood = "unlikely"
    return {
        "kp_index": kp,
        "time_tag": latest["time_tag"],
        "aurora_likelihood": likelihood,
    }


class AuroraForecastPlugin(Shitpost):
    """Fetch and emit the current planetary Kp-index. Skips the tick on any fetch failure."""

    name = "aurora-forecast"
    internal = False
    commit_template = "aurora: Kp={kp_index} ({aurora_likelihood})"

    def produce(self):
        try:
            with urllib.request.urlopen(ENDPOINT, timeout=10) as response:
                data = json.loads(response.read())
            return _parse(data)
        except Exception:
            return None
