import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class RupeeCostAveragingSimPlugin(Shitpost):
    """Simulate rupee-cost-averaging into an index over time."""

    name = "rupee-cost-averaging-sim"
    internal = False
    commit_template = "dca: tick {tick} invested {invested} value {current_value}"

    def __init__(self):
        super().__init__()

    def produce(self) -> dict:
        """Simulate rupee-cost-averaging and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state(default={"total_invested": 0, "total_units": 0, "tick": 0})

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

        self._save_persisted_state(state)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tick": state["tick"],
            "price": price,
            "invested": investment_amount,
            "units_bought": units_bought,
            "total_units": state["total_units"],
            "total_invested": state["total_invested"],
            "current_value": current_value,
            "pnl": pnl,
        }
