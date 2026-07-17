"""Enterprise near-duplicate detection engine powered by locality-sensitive AI hashing. Every fingerprint is a unique digital identity."""

import hashlib
import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class SimhashNearDupPlugin(Shitpost):
    """Compute Simhash fingerprints for a fixed cycling list of string pairs and report Hamming distance."""

    name = "simhash-near-dup"
    internal = False
    commit_template = "simhash({a}, {b}): distance={hamming_distance}"

    _BITS = 32
    _PAIRS = [
        ("the quick brown fox", "the quick brown fox jumps"),
        ("hello world", "goodbye world"),
        ("aaa bbb ccc", "aaa bbb ccc"),
    ]

    @classmethod
    def _simhash(cls, text: str) -> int:
        votes = [0] * cls._BITS
        for word in text.split():
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            for i in range(cls._BITS):
                votes[i] += 1 if (h >> i) & 1 else -1
        fingerprint = 0
        for i in range(cls._BITS):
            if votes[i] > 0:
                fingerprint |= (1 << i)
        return fingerprint

    @staticmethod
    def _hamming(a: int, b: int) -> int:
        return bin(a ^ b).count("1")

    def produce(self) -> dict:
        """Compute the Hamming distance for the current pair and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "pair_index": 0,
            "tick": 0,
        })

        a, b = self._PAIRS[state["pair_index"] % len(self._PAIRS)]
        distance = self._hamming(self._simhash(a), self._simhash(b))

        state["pair_index"] = (state["pair_index"] + 1) % len(self._PAIRS)
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "a": a,
            "b": b,
            "hamming_distance": distance,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
