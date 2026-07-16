"""Fetches current Bitcoin fee estimates from mempool.space's public API each tick."""

import json
import urllib.request

from harness.shitpost_base import Shitpost

ENDPOINT = "https://mempool.space/api/v1/fees/recommended"


def _parse(data):
    return {
        "fastest_fee": int(data["fastestFee"]),
        "half_hour_fee": int(data["halfHourFee"]),
        "hour_fee": int(data["hourFee"]),
        "economy_fee": int(data["economyFee"]),
        "minimum_fee": int(data["minimumFee"]),
    }


class BitcoinFeesPlugin(Shitpost):
    """Fetch and emit current Bitcoin fee estimates. Skips the tick on any fetch failure."""

    name = "bitcoin-fees"
    internal = False
    commit_template = "btc-fees: {fastest_fee} sat/vB fastest"

    def produce(self):
        try:
            with urllib.request.urlopen(ENDPOINT, timeout=10) as response:
                data = json.loads(response.read())
            return _parse(data)
        except Exception:
            return None
