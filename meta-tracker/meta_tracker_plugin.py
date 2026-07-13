import json
import os
import random
from datetime import datetime, timezone
from typing import Dict, List, Optional

from harness.shitpost_base import Shitpost


class MetaTrackerPlugin(Shitpost):
    """Track the 'meta' of a game by simulating tournaments and logging win rates."""

    name = "meta-tracker"
    internal = False
    commit_template = "meta: {n_strategies} strategies — leader {leader_name} ({leader_rate:.1%})"

    def __init__(self):
        super().__init__()
        self._state_file_name = "meta_state.json"
        self._log_file_name = "meta_log.jsonl"
        self._history_file_name = "meta_history.json"

    def _load_state(self, plugin_dir: str) -> Dict:
        """Load the running meta state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: meta state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"strategies", "matrix", "tick"}
            if not required.issubset(state.keys()):
                print(
                    "warning: meta state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> Dict:
        strategies = [
            {"name": "Rock", "wins": 0, "losses": 0},
            {"name": "Paper", "wins": 0, "losses": 0},
            {"name": "Scissors", "wins": 0, "losses": 0},
        ]
        matrix = [
            [0.5, 1.0, 0.0],
            [0.0, 0.5, 1.0],
            [1.0, 0.0, 0.5],
        ]
        return {
            "strategies": strategies,
            "matrix": matrix,
            "tick": 0,
        }

    def _save_state(self, plugin_dir: str, state: Dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _append_log(self, plugin_dir: str, log_entry: Dict) -> None:
        path = os.path.join(plugin_dir, self._log_file_name)
        with open(path, "a", encoding="utf-8") as f:
            json.dump(log_entry, f)
            f.write("\n")

    def _update_history(self, plugin_dir: str, strategy_name: str, win_rate: float) -> None:
        path = os.path.join(plugin_dir, self._history_file_name)
        if not os.path.exists(path):
            history = {}
        else:
            with open(path, "r", encoding="utf-8") as f:
                history = json.load(f)

        if strategy_name not in history:
            history[strategy_name] = []

        history[strategy_name].append({"date": datetime.now(timezone.utc).isoformat(), "win_rate": win_rate})

        with open(path, "w", encoding="utf-8") as f:
            json.dump(history, f)

    def _simulate_tournament(self, matrix: List[List[float]], strategies: List[Dict[str, str]]) -> Dict:
        total_matches = 0
        for i in range(len(strategies)):
            for j in range(i + 1, len(strategies)):
                n_matches = random.randint(50, 200)
                total_matches += n_matches

                for _ in range(n_matches):
                    if random.random() < matrix[i][j]:
                        strategies[i]["wins"] += 1
                    else:
                        strategies[j]["wins"] += 1

        return {
            "total_matches": total_matches,
            "strategies": strategies,
        }

    def produce(self) -> Optional[Dict]:
        """Simulate a tournament and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        matrix = state["matrix"]
        strategies = state["strategies"]

        result = self._simulate_tournament(matrix, strategies)
        total_matches = result["total_matches"]
        strategies = result["strategies"]

        # Update win rates
        for strategy in strategies:
            if total_matches > 0:
                win_rate = strategy["wins"] / total_matches
            else:
                win_rate = 0.5

            strategy["losses"] = total_matches - strategy["wins"]
            self._update_history(plugin_dir, strategy["name"], win_rate)

        # Update matrix with drift
        DRIFT_RATE = 0.02
        for i in range(len(strategies)):
            for j in range(i + 1, len(strategies)):
                observed_rate = strategies[i]["wins"] / total_matches if total_matches > 0 else 0.5
                matrix[i][j] = matrix[i][j] * (1 - DRIFT_RATE) + observed_rate * DRIFT_RATE
                matrix[j][i] = 1 - matrix[i][j]

        # Find leader
        leader_name = max(strategies, key=lambda x: x["wins"])["name"]
        leader_rate = strategies[strategy.index({"name": leader_name})]["wins"] / total_matches

        state["matrix"] = matrix
        state["tick"] += 1

        self._save_state(plugin_dir, state)

        return {
            "tick": state["tick"],
            "total_matches": total_matches,
            "leader_name": leader_name,
            "leader_rate": leader_rate,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
