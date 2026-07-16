"""Disrupted the ancient Egyptian numeral market with a greedy AI-powered fraction expansion platform. Each tick delivers stone-tablet-ready unit fractions."""

import math
import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class EgyptianFractionPlugin(Shitpost):
    """Emit one term of a rational's greedy Egyptian-fraction expansion per tick."""

    name = "egyptian-fraction"
    internal = False
    commit_template = "egyptian {rational}: term {term_index} = 1/{term_denominator}"

    # Fixed, deterministic sequence of rationals to expand (never user-supplied).
    _BASE_RATIONALS = [(4, 17), (5, 21), (3, 11), (7, 23), (2, 7), (5, 12), (3, 8), (7, 15)]

    def _next_rational(self, rational_index: int) -> tuple:
        """Return the (numerator, denominator) for the given index, cycling and
        offsetting the base list deterministically once exhausted."""
        base = self._BASE_RATIONALS[rational_index % len(self._BASE_RATIONALS)]
        cycle = rational_index // len(self._BASE_RATIONALS)
        return (base[0], base[1] + cycle * len(self._BASE_RATIONALS))

    def produce(self) -> dict:
        """Return the next Egyptian-fraction term and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "num": 0,
            "den": 1,
            "rational_index": -1,
            "orig_num": 0,
            "orig_den": 1,
            "term_index": 0,
            "tick": 0,
        })

        if state["num"] == 0:
            state["rational_index"] += 1
            orig_num, orig_den = self._next_rational(state["rational_index"])
            state["num"] = orig_num
            state["den"] = orig_den
            state["orig_num"] = orig_num
            state["orig_den"] = orig_den
            state["term_index"] = 0

        num, den = state["num"], state["den"]
        x = -(-den // num)  # ceiling division
        new_num = num * x - den
        new_den = den * x
        if new_num != 0:
            g = math.gcd(new_num, new_den)
            new_num //= g
            new_den //= g

        term_index = state["term_index"]
        orig_rational = f"{state['orig_num']}/{state['orig_den']}"

        state["num"] = new_num
        state["den"] = new_den
        state["term_index"] = term_index + 1
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "rational": orig_rational,
            "term_index": term_index,
            "term_denominator": x,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
