"""Logs BTC/ETH prices hourly so I can watch my hypothetical portfolio not exist in real time."""

import os
import sys
from datetime import datetime, timezone

import requests

from harness.shitpost_base import Shitpost


class CryptoTickPlugin(Shitpost):
    """Log BTC and ETH prices from CoinGecko API hourly."""

    name = "crypto-tick"
    internal = False
    commit_template = "crypto-tick: BTC ${btc_usd}, ETH ${eth_usd}"

    def produce(self) -> dict | None:
        """Fetch BTC and ETH prices from CoinGecko API."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "btc_usd": None,
            "eth_usd": None,
            "timestamp": None,
        })
        current_time = datetime.now(timezone.utc).isoformat()

        try:
            response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd")
            response.raise_for_status()
            data = response.json()
            btc_usd = data["bitcoin"]["usd"]
            eth_usd = data["ethereum"]["usd"]

            state["btc_usd"] = btc_usd
            state["eth_usd"] = eth_usd
            state["timestamp"] = current_time

        except requests.RequestException as e:
            print(f"warning: failed to fetch crypto prices ({e}); skipping tick", file=sys.stderr)
            return None

        self._save_persisted_state(state)

        return {
            "btc_usd": btc_usd,
            "eth_usd": eth_usd,
            "timestamp": current_time,
        }
