"""Fetches the current S&P 500 index value from Yahoo Finance's public chart API each tick."""

import json
import urllib.request

from harness.shitpost_base import Shitpost

ENDPOINT = "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC"


def _parse(data):
    meta = data["chart"]["result"][0]["meta"]
    price = float(meta["regularMarketPrice"])
    prev_close = float(meta["previousClose"])
    pct_change = (price - prev_close) / prev_close * 100
    return {
        "symbol": meta["symbol"],
        "price": round(price, 2),
        "previous_close": round(prev_close, 2),
        "pct_change": round(pct_change, 2),
    }


class StockIndexTickerPlugin(Shitpost):
    """Fetch and emit the current S&P 500 index value. Skips the tick on any fetch failure."""

    name = "stock-index-ticker"
    internal = False
    commit_template = "S&P 500: {price} ({pct_change:+.2f}%)"

    def produce(self):
        try:
            req = urllib.request.Request(ENDPOINT, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read())
            return _parse(data)
        except Exception:
            return None
