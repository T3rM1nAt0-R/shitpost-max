import json
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

    def __init__(self):
        super().__init__()
        self._state_file_name = "crypto_tick_state.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: crypto-tick state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"btc_usd", "eth_usd", "timestamp"}
            if not required.issubset(state.keys()):
                print(
                    "warning: crypto-tick state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "btc_usd": None,
            "eth_usd": None,
            "timestamp": None,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def produce(self) -> dict | None:
        """Fetch BTC and ETH prices from CoinGecko API."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
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

        self._save_state(plugin_dir, state)

        return {
            "btc_usd": btc_usd,
            "eth_usd": eth_usd,
            "timestamp": current_time,
        }
