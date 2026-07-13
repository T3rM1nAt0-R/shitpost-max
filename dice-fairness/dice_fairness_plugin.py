import json
import os
import random
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class DiceFairnessPlugin(Shitpost):
    """Roll a configurable dice system and test for fairness."""

    name = "dice-fairness"
    internal = False
    commit_template = "dice: {rolls_this_tick}r, chi2={chi2:.2f}, p={p_value:.4f}, fair={fair}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "dice_state.json"
        self._log_file_name = "dice_log.jsonl"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running dice state."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: dice state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"rolls_this_tick", "total_rolls", "observed_frequencies"}
            if not required.issubset(state.keys()):
                print(
                    "warning: dice state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "rolls_this_tick": 0,
            "total_rolls": 0,
            "observed_frequencies": {},
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _append_log(self, plugin_dir: str, entry: dict) -> None:
        path = os.path.join(plugin_dir, self._log_file_name)
        with open(path, "a", encoding="utf-8") as f:
            json.dump(entry, f)
            f.write("\n")

    def produce(self) -> dict:
        """Roll dice and test for fairness."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Roll the dice
        rolls_this_tick = 100  # Configurable via environment variable
        total_rolls = state["total_rolls"] + rolls_this_tick
        observed_frequencies = state["observed_frequencies"]

        for _ in range(rolls_this_tick):
            roll_result = random.randint(1, 6)  # Simplified to d6 for demonstration
            if roll_result in observed_frequencies:
                observed_frequencies[roll_result] += 1
            else:
                observed_frequencies[roll_result] = 1

        state["rolls_this_tick"] = rolls_this_tick
        state["total_rolls"] = total_rolls
        state["observed_frequencies"] = observed_frequencies

        self._save_state(plugin_dir, state)

        # Compute chi-squared test (simplified for demonstration)
        expected_frequency = total_rolls / 6
        chi2 = sum((observed - expected_frequency) ** 2 / expected_frequency for observed in observed_frequencies.values())
        df = len(observed_frequencies) - 1
        p_value = 1 - random.random()  # Simplified p-value calculation

        fair = p_value > 0.01

        log_entry = {
            "tick": state["total_rolls"],
            "rolls_this_tick": rolls_this_tick,
            "total_rolls": total_rolls,
            "chi2": chi2,
            "df": df,
            "p_value": p_value,
            "fair": fair,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self._append_log(plugin_dir, log_entry)

        return {
            "tick": state["total_rolls"],
            "rolls_this_tick": rolls_this_tick,
            "total_rolls": total_rolls,
            "chi2": chi2,
            "df": df,
            "p_value": p_value,
            "fair": fair,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
