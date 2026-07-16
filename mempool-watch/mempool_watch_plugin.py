"""Fetches current Bitcoin mempool unconfirmed tx count from mempool.space's public API each tick."""

import json
import urllib.request

from harness.shitpost_base import Shitpost

ENDPOINT = "https://mempool.space/api/mempool"


def _parse(data):
    return {
        "tx_count": int(data["count"]),
        "vsize": int(data["vsize"]),
        "total_fee": int(data["total_fee"]),
    }


class MempoolWatchPlugin(Shitpost):
    """Fetch and emit current mempool stats. Skips the tick on any fetch failure."""

    name = "mempool-watch"
    internal = False
    commit_template = "mempool: {tx_count} unconfirmed txs"

    def produce(self):
        try:
            with urllib.request.urlopen(ENDPOINT, timeout=10) as response:
                data = json.loads(response.read())
            return _parse(data)
        except Exception:
            return None
