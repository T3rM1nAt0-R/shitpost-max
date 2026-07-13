import json
import os
import random
from datetime import datetime, timezone
from typing import Dict, Optional

from harness.shitpost_base import Shitpost


class PlaytestBotPlugin(Shitpost):
    """Play one game of a toy game per tick and log the final score."""

    name = "playtest-bot"
    internal = False
    commit_template = "playtest [{agent}]: score {final_score} max {max_tile} in {game_length} moves"

    def __init__(self):
        super().__init__()
        self._state_file_name = "playtest_state.json"
        self._log_file_name = "playtest_log.jsonl"
        self._stats_file_name = "playtest_stats.json"

    def _load_state(self, plugin_dir: str) -> Dict[str, int]:
        """Load the running playtest state, or initialise it at tick 0."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: playtest state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"tick", "agent"}
            if not required.issubset(state.keys()):
                print(
                    "warning: playtest state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> Dict[str, int]:
        return {
            "tick": 0,
            "agent": 0,  # 0 for heuristic, 1 for random
        }

    def _save_state(self, plugin_dir: str, state: Dict[str, int]) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _append_log(self, plugin_dir: str, log_entry: Dict[str, int]) -> None:
        path = os.path.join(plugin_dir, self._log_file_name)
        with open(path, "a", encoding="utf-8") as f:
            json.dump(log_entry, f)
            f.write("\n")

    def _update_stats(self, plugin_dir: str, stats: Dict[str, int]) -> None:
        path = os.path.join(plugin_dir, self._stats_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def produce(self) -> Optional[Dict[str, int]]:
        """Return the result of playing one game and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        tick = state["tick"]
        agent = state["agent"]

        # Alternate between heuristic and random agents
        if agent == 0:
            result = self._play_game_heuristic()
        else:
            result = self._play_game_random()

        log_entry = {
            "tick": tick,
            "agent": "heuristic" if agent == 0 else "random",
            **result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self._append_log(plugin_dir, log_entry)

        # Update state
        state["tick"] += 1
        state["agent"] = 1 - agent  # Switch agent for next tick
        self._save_state(plugin_dir, state)

        return {
            "tick": tick,
            **result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _play_game_heuristic(self) -> Dict[str, int]:
        """Play one game using a heuristic agent."""
        # Implement the heuristic agent logic here
        pass

    def _play_game_random(self) -> Dict[str, int]:
        """Play one game using a random agent."""
        # Implement the random agent logic here
        pass
