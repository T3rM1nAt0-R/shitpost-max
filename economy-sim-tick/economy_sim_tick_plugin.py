"""Models a full supply-and-demand economy, one tick at a time. Inflation is a choice and I chose it."""

import json
import os
import random
from datetime import datetime, timezone

import yaml

from harness.shitpost_base import Shitpost


class EconomySimTickPlugin(Shitpost):
    """Run one step of a toy supply/demand simulation per tick."""

    name = "economy-sim-tick"
    internal = False
    commit_template = "econ [{regime}]: P={price:.2f} Q={quantity:.2f} CS={consumer_surplus:.2f} PS={producer_surplus:.2f}"

    def __init__(self):
        super().__init__()
        self._log_file_name = "economy_log.jsonl"

    def _persisted_state_path(self) -> str:
        return os.path.join(self._plugin_dir(), "economy_state.json")

    def _append_log(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._log_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(state) + "\n")

    def produce(self) -> dict:
        """Run one step of the economy simulation and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "price": 0.0,
            "quantity": 0.0,
            "prev_price": 0.0,
            "tick": 0,
        })

        # Load curves from config
        with open(os.path.join(plugin_dir, "curves.yaml"), "r", encoding="utf-8") as f:
            curves = yaml.safe_load(f)
        a_d, b_d = curves["demand"]["intercept"], curves["demand"]["slope"]
        a_s, b_s = curves["supply"]["intercept"], curves["supply"]["slope"]

        # Compute quantity from previous price
        state["quantity"] = (state["prev_price"] - a_s) / b_s

        # Compute price from current quantity
        state["price"] = a_d - b_d * state["quantity"]

        # Apply shock if enabled
        if os.getenv("SHOCK_ENABLED", "false").lower() == "true":
            shock_stddev = float(os.getenv("SHOCK_STDDEV", "0.05"))
            state["price"] += random.gauss(0, shock_stddev)

        # Compute surpluses
        consumer_surplus = 0.5 * (curves["demand"]["intercept"] - state["price"]) * state["quantity"]
        producer_surplus = 0.5 * (state["price"] - curves["supply"]["intercept"]) * state["quantity"]
        total_surplus = consumer_surplus + producer_surplus

        # Determine regime
        if abs(state["price"] - state["prev_price"]) < 1e-6:
            regime = "converging"
        elif abs(state["price"] - state["prev_price"]) > 10:
            regime = "diverging"
        else:
            regime = "oscillating"

        # Update state
        state["tick"] += 1
        state["prev_price"] = state["price"]

        self._save_persisted_state(state)
        self._append_log(plugin_dir, {
            "tick": state["tick"],
            "price": state["price"],
            "quantity": state["quantity"],
            "prev_price": state["prev_price"],
            "consumer_surplus": consumer_surplus,
            "producer_surplus": producer_surplus,
            "total_surplus": total_surplus,
            "regime": regime,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        return {
            "tick": state["tick"],
            "price": state["price"],
            "quantity": state["quantity"],
            "prev_price": state["prev_price"],
            "consumer_surplus": consumer_surplus,
            "producer_surplus": producer_surplus,
            "total_surplus": total_surplus,
            "regime": regime,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
