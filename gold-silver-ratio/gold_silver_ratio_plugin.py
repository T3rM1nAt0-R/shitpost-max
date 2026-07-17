"""Fetches gold and silver spot prices from a public API each tick and computes their ratio."""

import json
import urllib.request

from harness.shitpost_base import Shitpost

GOLD_URL = "https://api.gold-api.com/price/XAU"
SILVER_URL = "https://api.gold-api.com/price/XAG"


def _parse(gold_data, silver_data):
    gold_price = float(gold_data["price"])
    silver_price = float(silver_data["price"])
    return {
        "gold_price": gold_price,
        "silver_price": silver_price,
        "ratio": round(gold_price / silver_price, 2),
    }


class GoldSilverRatioPlugin(Shitpost):
    """Fetch and emit the current gold/silver price ratio. Skips the tick on any fetch failure."""

    name = "gold-silver-ratio"
    internal = False
    commit_template = "gold/silver ratio: {ratio}"

    def produce(self):
        try:
            with urllib.request.urlopen(GOLD_URL, timeout=10) as response:
                gold_data = json.loads(response.read())
            with urllib.request.urlopen(SILVER_URL, timeout=10) as response:
                silver_data = json.loads(response.read())
            return _parse(gold_data, silver_data)
        except Exception:
            return None
