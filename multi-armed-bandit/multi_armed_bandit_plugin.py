"""AI-optimized sequential decision-making platform for enterprise exploration-exploitation tradeoffs. Every pull is a resource allocation decision."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class MultiArmedBanditPlugin(Shitpost):
    """Run a deterministic epsilon-first multi-armed bandit over 3 fixed-reward arms."""

    name = "multi-armed-bandit"
    internal = False
    commit_template = "bandit pull arm {arm}: reward {reward}"

    _ARM_REWARDS = [1, 5, 3]

    def produce(self) -> dict:
        """Pull the next bandit arm and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        num_arms = len(self._ARM_REWARDS)
        state = self._load_persisted_state({
            "pulls": [0] * num_arms,
            "totals": [0] * num_arms,
            "tick_count": 0,
            "tick": 0,
        })

        tick_count = state["tick_count"]
        if tick_count < num_arms:
            arm = tick_count
        else:
            avgs = [
                state["totals"][i] / state["pulls"][i] if state["pulls"][i] > 0 else -1
                for i in range(num_arms)
            ]
            arm = avgs.index(max(avgs))

        reward = self._ARM_REWARDS[arm]
        state["pulls"][arm] += 1
        state["totals"][arm] += reward
        state["tick_count"] += 1
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "arm": arm,
            "reward": reward,
            "pulls": list(state["pulls"]),
            "totals": list(state["totals"]),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
