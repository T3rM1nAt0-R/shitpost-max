"""Revolutionizing game-theoretic strategy optimization with an AI-mediated iterated dilemma engine. Every round is a trust-building exercise."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class IteratedPrisonerPlugin(Shitpost):
    """Run one round of Iterated Prisoner's Dilemma between Tit-for-Tat and Always-Defect."""

    name = "iterated-prisoner"
    internal = False
    commit_template = "prisoner round {tick}: A={a_move}({a_score}) B={b_move}({b_score})"

    @staticmethod
    def _payoff(a: str, b: str) -> tuple:
        if a == "C" and b == "C":
            return 3, 3
        if a == "D" and b == "D":
            return 1, 1
        if a == "C" and b == "D":
            return 0, 5
        return 5, 0

    def produce(self) -> dict:
        """Play one round and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "a_history": [],
            "b_history": [],
            "a_score": 0,
            "b_score": 0,
            "tick": 0,
        })

        a_move = state["b_history"][-1] if state["b_history"] else "C"
        b_move = "D"

        pa, pb = self._payoff(a_move, b_move)
        state["a_score"] += pa
        state["b_score"] += pb
        state["a_history"].append(a_move)
        state["b_history"].append(b_move)
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "a_move": a_move,
            "b_move": b_move,
            "a_score": state["a_score"],
            "b_score": state["b_score"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
