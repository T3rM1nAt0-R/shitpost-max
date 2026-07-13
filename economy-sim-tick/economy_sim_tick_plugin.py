import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class EconomySimTickPlugin(Shitpost):
    """Run one step of a toy supply/demand simulation per tick."""

    name = "economy-sim-tick"
    internal = False
    commit_template = "econ [{regime}]: P={price:.2f} Q={quantity:.2f} CS={consumer_surplus:.2f} PS={producer_surplus:.2f}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "economy_state.json"
        self._log_file_name = "economy_log.jsonl"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running economy state."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: economy state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"price", "quantity", "prev_price", "tick"}
            if not required.issubset(state.keys()):
                print(
                    "warning: economy state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "price": 0.0,
            "quantity": 0.0,
            "prev_price": 0.0,
            "tick": 0,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _append_log(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._log_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(state) + "\n")

    def produce(self) -> dict:
        """Run one step of the economy simulation and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

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
            state["price"] += np.random.normal(0, shock_stddev)

        # Compute surpluses
        consumer_surplus = 0.5 * (state["prev_price"] + state["price"]) * (state["quantity"] - curves["demand"]["intercept"] / curves["demand"]["slope"])
        producer_surplus = 0.5 * (state["price"] - curves["supply"]["intercept"] / curves["supply"]["slope"]) * state["quantity"]
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

        self._save_state(plugin_dir, state)
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
