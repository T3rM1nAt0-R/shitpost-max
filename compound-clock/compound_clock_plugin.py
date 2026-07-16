"""Compounds a hypothetical investment per tick, because watching imaginary money grow is still money growing."""

import os
from datetime import datetime, timezone
from decimal import Decimal, getcontext

getcontext().prec = 28

from harness.shitpost_base import Shitpost


class CompoundClockPlugin(Shitpost):
    """Emit the compound value of an investment per tick."""

    name = "compound-clock"
    internal = False
    commit_template = "compound: day {day} = {value}"

    def __init__(self):
        super().__init__()

    @staticmethod
    def compound_value(principal: Decimal, annual_rate: Decimal, day: int) -> Decimal:
        daily_rate = annual_rate / Decimal(365)
        return principal * (Decimal(1) + daily_rate) ** day

    @staticmethod
    def _default_state() -> dict:
        return {
            "day": 0,
            "tick": 0,
        }

    def produce(self) -> dict:
        """Return the compound value and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state(default=self._default_state())

        # Read config from environment variables with defaults
        principal = Decimal(os.environ.get("PRINCIPAL", "1000"))
        annual_rate = Decimal(os.environ.get("ANNUAL_RATE", "0.05"))
        max_days = int(os.environ.get("MAX_DAYS", "30"))

        # Compute the compound value
        day = state["day"]
        if day >= max_days:
            value = self.compound_value(principal, annual_rate, max_days)
        else:
            value = self.compound_value(principal, annual_rate, day)

        # Advance day and tick if not at max_days
        if day < max_days:
            state["day"] += 1
        state["tick"] += 1

        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "day": day,
            "value": str(value),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
