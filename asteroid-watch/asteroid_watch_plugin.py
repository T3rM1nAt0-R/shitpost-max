"""Fetches today's near-Earth asteroid close-approach data from NASA's NeoWs API each tick."""

import json
import urllib.request

from harness.shitpost_base import Shitpost

ENDPOINT = "https://api.nasa.gov/neo/rest/v1/feed/today?api_key=DEMO_KEY"


def _parse(data):
    date = next(iter(data["near_earth_objects"]))
    objects = data["near_earth_objects"][date]
    if not objects:
        raise ValueError("no near-earth objects for today")
    extracted = []
    for obj in objects:
        miss_km = float(obj["close_approach_data"][0]["miss_distance"]["kilometers"])
        extracted.append((obj["name"], miss_km, obj["is_potentially_hazardous_asteroid"]))
    closest = min(extracted, key=lambda o: o[1])
    return {
        "element_count": data["element_count"],
        "closest_name": closest[0],
        "closest_miss_km": closest[1],
        "closest_hazardous": closest[2],
    }


class AsteroidWatchPlugin(Shitpost):
    """Fetch and emit today's closest near-Earth asteroid approach. Skips the tick on any fetch failure."""

    name = "asteroid-watch"
    internal = False
    commit_template = "asteroids today: {element_count}, closest {closest_name} ({closest_miss_km} km)"

    def produce(self):
        try:
            with urllib.request.urlopen(ENDPOINT, timeout=15) as response:
                data = json.loads(response.read())
            return _parse(data)
        except Exception:
            return None
