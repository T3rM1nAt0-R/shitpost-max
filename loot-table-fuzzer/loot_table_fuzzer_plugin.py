import json
import os
import random
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class LootTableFuzzerPlugin(Shitpost):
    """Pull one random drop per tick from a weighted loot table and log running drop-rate observations."""

    name = "loot-table-fuzzer"
    internal = False
    commit_template = "loot: {item} (observed {observed_rate:.2%} vs expected {weight:.2%})"

    def __init__(self):
        super().__init__()
        self._state_file_name = "loot_state.json"
        self._log_file_name = "loot_log.jsonl"
        self._rates_file_name = "loot_rates.json"
        self._tick_seconds = int(os.getenv("TICK_SECONDS", 60))
        self._check_interval = int(os.getenv("CHECK_INTERVAL", 1000))

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running loot state."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: loot state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"total_rolls", "items"}
            if not required.issubset(state.keys()):
                print(
                    "warning: loot state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "total_rolls": 0,
            "items": {}
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _append_log(self, plugin_dir: str, item: str, weight: float) -> None:
        path = os.path.join(plugin_dir, self._log_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "tick": self.tick,
                "item": item,
                "weight": weight,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }) + "\n")

    def _update_rates(self, plugin_dir: str, item: str, weight: float) -> None:
        path = os.path.join(plugin_dir, self._rates_file_name)
        with open(path, "r", encoding="utf-8") as f:
            rates = json.load(f)

        total_rolls = rates["total_rolls"] + 1
        item_rates = rates["items"].get(item, {"weight": weight, "observed_rate": 0.0, "count": 0})
        item_rates["count"] += 1
        item_rates["observed_rate"] = item_rates["count"] / total_rolls

        rates["total_rolls"] = total_rolls
        rates["items"][item] = item_rates

        with open(path, "w", encoding="utf-8") as f:
            json.dump(rates, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")

    def _compute_deviation(self, plugin_dir: str) -> None:
        path = os.path.join(plugin_dir, self._rates_file_name)
        with open(path, "r", encoding="utf-8") as f:
            rates = json.load(f)

        print("Deviation Summary:")
        for item, rate in rates["items"].items():
            deviation = abs(rate["observed_rate"] - (rate["weight"] / 100))
            print(f"{item}: {deviation:.2%}")

    def produce(self) -> dict:
        """Return the next loot drop and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        loot_table = [
            {"item": "Common Item", "weight": 80},
            {"item": "Uncommon Item", "weight": 15},
            {"item": "Rare Item", "weight": 4}
        ]

        total_weight = sum(item["weight"] for item in loot_table)
        rand = random.uniform(0, total_weight)
        cumulative_weight = 0
        selected_item = None

        for item in loot_table:
            cumulative_weight += item["weight"]
            if rand <= cumulative_weight:
                selected_item = item
                break

        state["total_rolls"] += 1
        self._save_state(plugin_dir, state)
        self._append_log(plugin_dir, selected_item["item"], selected_item["weight"])
        self._update_rates(plugin_dir, selected_item["item"], selected_item["weight"])

        if self.tick % self._check_interval == 0:
            self._compute_deviation(plugin_dir)

        return {
            "tick": state["total_rolls"],
            "item": selected_item["item"],
            "weight": selected_item["weight"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
