import json
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
        self._state_file_name = "usd_inr_state.json"
        self._rates_file_name = "usd_inr_rates.txt"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running USD/INR state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: usd-inr state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"rate", "timestamp"}
            if not required.issubset(state.keys()):
                print(
                    "warning: usd-inr state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "rate": None,
            "timestamp": None,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _append_rate(self, plugin_dir: str, rate: float) -> None:
        path = os.path.join(plugin_dir, self._rates_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now(timezone.utc).isoformat()}, {rate}\n")

    def produce(self) -> dict:
        """Return the USD/INR exchange rate and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

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

        self._save_state(plugin_dir, state)
        self._append_rate(plugin_dir, rate)

        return {
            "tick": 1,
            "rate": rate,
            "timestamp": state["timestamp"],
        }
