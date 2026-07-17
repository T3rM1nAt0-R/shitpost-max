"""Fetches a current COVID-19 wastewater viral concentration data point from the CDC's public API each tick."""

import json
import urllib.request

from harness.shitpost_base import Shitpost

ENDPOINT = "https://data.cdc.gov/resource/2ew6-ywp6.json?%24limit=1"


def _parse(records):
    if not records:
        raise ValueError("empty records list")
    r = records[0]
    return {
        "jurisdiction": r["wwtp_jurisdiction"],
        "percentile": float(r["percentile"]),
        "date_start": r["date_start"],
        "date_end": r["date_end"],
    }


class CovidWastewaterPlugin(Shitpost):
    """Fetch and emit a current COVID-19 wastewater data point. Skips the tick on any fetch failure."""

    name = "covid-wastewater"
    internal = False
    commit_template = "wastewater {jurisdiction}: {percentile} percentile"

    def produce(self):
        try:
            with urllib.request.urlopen(ENDPOINT, timeout=10) as response:
                data = json.loads(response.read())
            return _parse(data)
        except Exception:
            return None
