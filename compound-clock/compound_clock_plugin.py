import json
import os
import sys
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
        self._state_file_name = "compound_clock_state.json"

    @staticmethod
    def compound_value(principal: Decimal, annual_rate: Decimal, day: int) -> Decimal:
        daily_rate = annual_rate / Decimal(365)
        return principal * (Decimal(1) + daily_rate) ** day

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running compound clock state, or initialise it at day 0."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: compound clock state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"day", "tick"}
            if not required.issubset(state.keys()):
                print(
                    "warning: compound clock state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "day": 0,
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
        """Return the compound value and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

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

        self._save_state(plugin_dir, state)

        return {
            "tick": state["tick"],
            "day": day,
            "value": str(value),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


