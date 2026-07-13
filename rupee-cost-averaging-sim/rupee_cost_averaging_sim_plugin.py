import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class RupeeCostAveragingSimPlugin(Shitpost):
    """Simulate rupee-cost-averaging into an index over time."""

    name = "rupee-cost-averaging-sim"
    internal = False
    commit_template = "dca: tick {tick} invested {invested} value {current_value}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "dca_state.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running DCA state, or initialise it at tick 0."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: dca state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"total_invested", "total_units", "tick"}
            if not required.issubset(state.keys()):
                print(
                    "warning: dca state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "total_invested": 0,
            "total_units": 0,
            "tick": 0,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def produce(self) -> dict:
        """Simulate rupee-cost-averaging and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Simulate investment
        investment_amount = int(os.getenv("INVESTMENT_AMOUNT", 100))
        price = float(os.getenv("PRICE_SOURCE", "100"))
        units_bought = investment_amount / price

        # Update running totals
        state["total_invested"] += investment_amount
        state["total_units"] += units_bought
        state["tick"] += 1

        current_value = state["total_units"] * price
        pnl = current_value - state["total_invested"]

        self._save_state(plugin_dir, state)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "price": price,
            "invested": investment_amount,
            "units_bought": units_bought,
            "total_units": state["total_units"],
            "total_invested": state["total_invested"],
            "current_value": current_value,
            "pnl": pnl,
        }
