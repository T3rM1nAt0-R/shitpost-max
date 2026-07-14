import json
import os
import random
from datetime import datetime, timezone
from typing import Dict, Optional

from harness.shitpost_base import Shitpost


class GachaOraclePlugin(Shitpost):
    """Simulate one gacha pull per tick against configurable rates."""

    name = "gacha-oracle"
    internal = False
    commit_template = "gacha: pull {tick} = {outcome} (pity {pity_at_pull})"

    def __init__(self):
        super().__init__()
        self._log_file_name = "gacha_log.jsonl"
        self._stats_file_name = "gacha_stats.json"

    def _persisted_state_path(self) -> str:
        """Override to preserve the original custom state filename."""
        return os.path.join(self._plugin_dir(), "gacha_state.json")

    def _log_pull(self, plugin_dir: str, tick: int, outcome: str, rarity: str, pity_at_pull: int, guarantee_used: bool) -> None:
        path = os.path.join(plugin_dir, self._log_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "tick": tick,
                "outcome": outcome,
                "rarity": rarity,
                "pity_at_pull": pity_at_pull,
                "guarantee_used": guarantee_used,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }) + "\n")

    def _update_stats(self, plugin_dir: str, state: Dict) -> None:
        path = os.path.join(plugin_dir, self._stats_file_name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)

    def produce(self) -> Optional[Dict]:
        """Return the result of one gacha pull and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({"pity": 0, "total_pulls": 0, "total_5star": 0, "current_pity": 0})
        tick = state["total_pulls"] + 1

        # Increment pity counter
        state["pity"] += 1
        state["current_pity"] += 1

        # Calculate effective rate
        base_rate = float(os.getenv("BASE_RATE", "0.006"))
        soft_pity = int(os.getenv("SOFT_PITY", "75"))
        hard_pity = int(os.getenv("HARD_PITY", "90"))
        if state["current_pity"] >= hard_pity:
            effective_rate = 1.0
        elif state["current_pity"] >= soft_pity:
            effective_rate = base_rate + (state["current_pity"] - soft_pity) / (hard_pity - soft_pity) * (1 - base_rate)
        else:
            effective_rate = base_rate

        # Perform the pull
        outcome = "hit" if random.random() < effective_rate else "miss"
        rarity = "5star" if outcome == "hit" and random.random() < 0.6 else "4star"
        guarantee_used = False
        if state["current_pity"] >= hard_pity:
            guarantee_used = True
            state["pity"] = 0

        # Log the pull
        self._log_pull(plugin_dir, tick, outcome, rarity, state["current_pity"], guarantee_used)

        # Update statistics
        state["total_pulls"] += 1
        if outcome == "hit":
            state["total_5star"] += 1
        state["pity_histogram"] = state.get("pity_histogram", {})
        state["pity_histogram"][str(state["current_pity"])] = state["pity_histogram"].get(str(state["current_pity"]), 0) + 1

        # Reset pity counter if guaranteed hit
        if guarantee_used:
            state["current_pity"] = 0

        self._save_persisted_state(state)
        self._update_stats(plugin_dir, state)

        return {
            "tick": tick,
            "outcome": outcome,
            "rarity": rarity,
            "pity_at_pull": state["current_pity"],
            "guarantee_used": guarantee_used,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
