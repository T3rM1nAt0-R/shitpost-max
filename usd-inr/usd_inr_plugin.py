import os
import sys
from datetime import datetime, timezone
import requests

from harness.shitpost_base import Shitpost


class UsdInrPlugin(Shitpost):
    """Emit the USD/INR exchange rate per tick."""

    name = "usd-inr"
    internal = False
    commit_template = "usd-inr: {rate} INR per USD"

    def __init__(self):
        super().__init__()
        self._rates_file_name = "usd_inr_rates.txt"

    def _append_rate(self, plugin_dir: str, rate: float) -> None:
        path = os.path.join(plugin_dir, self._rates_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now(timezone.utc).isoformat()}, {rate}\n")

    def produce(self) -> dict:
        """Return the USD/INR exchange rate and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({"rate": None, "timestamp": None})

        # Fetch the current USD/INR rate
        response = requests.get(os.getenv("SOURCE_URL", "https://open.er-api.com/v6/latest/USD"))
        if response.status_code != 200:
            print(f"warning: failed to fetch USD/INR rate ({response.status_code})", file=sys.stderr)
            return None

        data = response.json()
        if "rates" not in data or "INR" not in data["rates"]:
            print("warning: invalid USD/INR rate data", file=sys.stderr)
            return None

        rate = data["rates"]["INR"]
        state["rate"] = rate
        state["timestamp"] = datetime.now(timezone.utc).isoformat()

        self._save_persisted_state(state)
        self._append_rate(plugin_dir, rate)

        return {
            "tick": 1,
            "rate": rate,
            "timestamp": state["timestamp"],
        }
