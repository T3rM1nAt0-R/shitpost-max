"""AI-driven string alignment platform bringing edit distance computation to the enterprise. Disrupting the spell-check industry one insertion at a time."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class LevenshteinWatchPlugin(Shitpost):
    """Compute the Levenshtein distance for a fixed, cycling list of string pairs."""

    name = "levenshtein-watch"
    internal = False
    commit_template = "levenshtein({a}, {b}) = {distance}"

    _PAIRS = [
        ("kitten", "sitting"),
        ("flaw", "lawn"),
        ("intention", "execution"),
        ("abc", "abc"),
        ("", "abc"),
    ]

    @staticmethod
    def _levenshtein(a: str, b: str) -> int:
        m, n = len(a), len(b)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if a[i - 1] == b[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
        return dp[m][n]

    def produce(self) -> dict:
        """Return the Levenshtein distance for the current pair and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "pair_index": 0,
            "tick": 0,
        })

        a, b = self._PAIRS[state["pair_index"] % len(self._PAIRS)]
        distance = self._levenshtein(a, b)

        state["pair_index"] = (state["pair_index"] + 1) % len(self._PAIRS)
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "a": a,
            "b": b,
            "distance": distance,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
