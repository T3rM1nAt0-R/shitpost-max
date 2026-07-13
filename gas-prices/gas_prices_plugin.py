import json
import os
import sys
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import requests

from harness.shitpost_base import Shitpost


class GasPricesPlugin(Shitpost):
    """Track utility/fuel cost over time, logged daily to JSONL."""

    name = "gas-prices"
    internal = False
    commit_template = "gas-prices: {fuel_type} {price} {currency} at {location}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "gas_prices_state.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: gas prices state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"timestamp", "location", "fuel_type", "price", "currency", "source"}
            if not required.issubset(state.keys()):
                print(
                    "warning: gas prices state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "timestamp": None,
            "location": None,
            "fuel_type": None,
            "price": None,
            "currency": None,
            "source": None,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def produce(self) -> dict | None:
        """Fetch fuel price and update persistent state."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        location = os.getenv("LOCATION", "Bangalore")
        fuel_type = os.getenv("FUEL_TYPE", "Petrol")
        source_url = os.getenv("SOURCE_URL", "https://iocl.com/Products/PetrolPriceInMetros.aspx")

        try:
            response = requests.get(source_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'class': 'priceTable'})
            if not table:
                print("Error: Unable to find price table on the page.", file=sys.stderr)
                return None

            rows = table.find_all('tr')[1:]  # Skip header row
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3 and cols[0].text.strip() == location:
                    price = float(cols[2].text.strip().replace(',', ''))
                    currency = "INR"
                    state["timestamp"] = datetime.now(timezone.utc).isoformat()
                    state["location"] = location
                    state["fuel_type"] = fuel_type
                    state["price"] = price
                    state["currency"] = currency
                    state["source"] = source_url

                    self._save_state(plugin_dir, state)
                    return {
                        "timestamp": state["timestamp"],
                        "location": state["location"],
                        "fuel_type": state["fuel_type"],
                        "price": state["price"],
                        "currency": state["currency"],
                        "source": state["source"]
                    }

        except requests.RequestException as e:
            print(f"Error: Failed to fetch price data ({e}).", file=sys.stderr)
            return None

        return None
