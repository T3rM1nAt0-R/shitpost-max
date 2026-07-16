"""Revolutionizing substring search with an AI-powered linear-time pattern matching engine. Each failure function entry is a strategic pivot."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class KnuthMorrisPrattPlugin(Shitpost):
    """Run the KMP string-matching algorithm against a fixed, cycling list of pattern/text pairs."""

    name = "knuth-morris-pratt"
    internal = False
    commit_template = "kmp {pattern}: {match_count} matches"

    _PAIRS = [
        ("ABABCABAB", "ABABDABACDABABCABABIRHOJIABABCABABX"),
        ("AABAACAABAA", "AABAACAABAAAABAACAABAA"),
        ("ABAB", "ABABABAB"),
    ]

    @staticmethod
    def _kmp_failure(pattern: str) -> list:
        n = len(pattern)
        fail = [0] * n
        k = 0
        for i in range(1, n):
            while k > 0 and pattern[i] != pattern[k]:
                k = fail[k - 1]
            if pattern[i] == pattern[k]:
                k += 1
            fail[i] = k
        return fail

    @classmethod
    def _kmp_search(cls, text: str, pattern: str) -> list:
        fail = cls._kmp_failure(pattern)
        matches = []
        k = 0
        for i, ch in enumerate(text):
            while k > 0 and ch != pattern[k]:
                k = fail[k - 1]
            if ch == pattern[k]:
                k += 1
            if k == len(pattern):
                matches.append(i - len(pattern) + 1)
                k = fail[k - 1]
        return matches

    def produce(self) -> dict:
        """Return the KMP failure function and matches for the current pair, and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "pair_index": 0,
            "tick": 0,
        })

        pattern, text = self._PAIRS[state["pair_index"] % len(self._PAIRS)]
        failure = self._kmp_failure(pattern)
        matches = self._kmp_search(text, pattern)

        state["pair_index"] = (state["pair_index"] + 1) % len(self._PAIRS)
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "pattern": pattern,
            "failure": failure,
            "matches": matches,
            "match_count": len(matches),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
