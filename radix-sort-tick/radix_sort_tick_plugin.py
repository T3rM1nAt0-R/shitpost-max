"""Disintermediated comparison-based sorting with an LSD-first radix sort engine. Sorting by digits, not by judgment calls."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class RadixSortTickPlugin(Shitpost):
    """Perform one LSD radix-sort digit pass per tick on a fixed array, resetting once fully sorted."""

    name = "radix-sort-tick"
    internal = False
    commit_template = "radix pass exp={pass_exp}: {array}"

    _ARRAY = [170, 45, 75, 90, 802, 24, 2, 66]

    @staticmethod
    def _radix_pass(arr: list, exp: int) -> list:
        output = [0] * len(arr)
        count = [0] * 10
        for n in arr:
            idx = (n // exp) % 10
            count[idx] += 1
        for i in range(1, 10):
            count[i] += count[i - 1]
        for n in reversed(arr):
            idx = (n // exp) % 10
            count[idx] -= 1
            output[count[idx]] = n
        return output

    def produce(self) -> dict:
        """Apply the next radix-sort digit pass and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "arr": list(self._ARRAY),
            "exp": 1,
            "tick": 0,
        })

        exp = state["exp"]
        arr = self._radix_pass(state["arr"], exp)
        is_sorted = max(arr) // (exp * 10) == 0

        if is_sorted:
            state["arr"] = list(self._ARRAY)
            state["exp"] = 1
        else:
            state["arr"] = arr
            state["exp"] = exp * 10

        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "pass_exp": exp,
            "array": arr,
            "sorted": is_sorted,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
