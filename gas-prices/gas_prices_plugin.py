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

    def produce(self) -> dict | None:
        """Fetch fuel price and update persistent state."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "timestamp": None,
            "location": None,
            "fuel_type": None,
            "price": None,
            "currency": None,
            "source": None,
        })

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

                    self._save_persisted_state(state)
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
