import json
import os
import random
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional

from harness.shitpost_base import Shitpost


class BalanceWitnessPlugin(Shitpost):
    """Simulate one match of a toy auto-battler per tick using unit stats and simple combat rules."""

    name = "balance-witness"
    internal = False
    commit_template = "balance: {winner_archetype} beats {loser_archetype} in {turns} turns"

    def __init__(self):
        super().__init__()
        self._state_file_name = "balance_state.json"
        self._log_file_name = "match_log.jsonl"
        self._stats_file_name = "balance_stats.json"

    @staticmethod
    def _default_roster() -> Dict[str, Dict]:
        return {
            "Warrior": {"hp": 100, "atk": 20, "def": 15, "speed": 8},
            "Mage": {"hp": 75, "atk": 30, "def": 5, "speed": 10},
            "Archer": {"hp": 60, "atk": 25, "def": 10, "speed": 12},
        }

    @staticmethod
    def _default_stats() -> Dict:
        return {
            "total_matches": 0,
            "unit_stats": {},
            "archetype_stats": {}
        }

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it at default values."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: balance state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"total_matches", "unit_stats", "archetype_stats"}
            if not required.issubset(state.keys()):
                print(
                    "warning: balance state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "total_matches": 0,
            "unit_stats": {},
            "archetype_stats": {}
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
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

    def _update_stats(self, plugin_dir: str, winner_archetype: str, loser_archetype: str) -> None:
        path = os.path.join(plugin_dir, self._stats_file_name)
        state = self._load_state(plugin_dir)

        # Update total matches
        state["total_matches"] += 1

        # Update unit stats
        for unit in winner_archetype.split(","):
            if unit not in state["unit_stats"]:
                state["unit_stats"][unit] = {"wins": 0, "losses": 0, "pick_count": 0}
            state["unit_stats"][unit]["wins"] += 1

        for unit in loser_archetype.split(","):
            if unit not in state["unit_stats"]:
                state["unit_stats"][unit] = {"wins": 0, "losses": 0, "pick_count": 0}
            state["unit_stats"][unit]["losses"] += 1

        # Update archetype stats
        if winner_archetype not in state["archetype_stats"]:
            state["archetype_stats"][winner_archetype] = {"wins": 0, "losses": 0}
        state["archetype_stats"][winner_archetype]["wins"] += 1

        if loser_archetype not in state["archetype_stats"]:
            state["archetype_stats"][loser_archetype] = {"wins": 0, "losses": 0}
        state["archetype_stats"][loser_archetype]["losses"] += 1

        self._save_state(plugin_dir, state)

    def _simulate_combat(self, team1: List[str], team2: List[str]):
        """Simulate combat and return (winner_team_str, turn_count)."""
        roster = self._default_roster()
        turn_order = sorted(team1 + team2, key=lambda unit: -roster[unit]["speed"])
        alive_units = set(turn_order)
        turns = 0

        while len(alive_units) > 1:
            for unit in turn_order:
                if unit not in alive_units:
                    continue
                target = min(alive_units, key=lambda u: roster[u]["hp"])
                damage = max(1, roster[unit]["atk"] - roster[target]["def"])
                roster[target]["hp"] -= damage
                if roster[target]["hp"] <= 0:
                    alive_units.remove(target)
            turns += 1

        return ",".join(alive_units), turns

    def produce(self) -> Optional[Dict]:
        """Simulate one match and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Compose two random teams
        roster = list(self._default_roster().keys())
        team1 = random.sample(roster, k=3)
        team2 = random.sample(roster, k=3)

        # Simulate combat and determine the winner
        winner_team, turns = self._simulate_combat(team1, team2)
        loser_team = ",".join(set(team1 + team2) - set(winner_team.split(",")))
        winner_archetype = ",".join(sorted(winner_team))
        loser_archetype = ",".join(sorted(loser_team))

        # Log the match result
        log_entry = {
            "tick": state["total_matches"],
            "winner_team": winner_team,
            "winner_archetype": winner_archetype,
            "survivors": winner_team,
            "turns": turns,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self._append_log(plugin_dir, log_entry)

        # Update win-rate statistics
        self._update_stats(plugin_dir, winner_archetype, loser_archetype)

        return {
            "tick": state["total_matches"],
            "winner_team": winner_team,
            "winner_archetype": winner_archetype,
            "survivors": winner_team,
            "turns": turns,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
