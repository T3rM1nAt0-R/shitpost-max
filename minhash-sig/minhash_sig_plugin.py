"""AI-enhanced set similarity estimation platform disrupting the Jaccard index market. Every signature is a probabilistic guarantee."""

import hashlib
import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class MinhashSigPlugin(Shitpost):
    """Compute MinHash signatures for two fixed sets and compare estimated vs true Jaccard similarity."""

    name = "minhash-sig"
    internal = False
    commit_template = "minhash: est={estimated_jaccard} true={true_jaccard}"

    _NUM_HASHES = 8
    _SET_A = {"apple", "banana", "cherry", "date"}
    _SET_B = {"banana", "cherry", "date", "elderberry", "fig"}

    @classmethod
    def _minhash_signature(cls, items: set) -> list:
        sig = []
        for i in range(cls._NUM_HASHES):
            min_val = None
            for item in items:
                h = int(hashlib.md5(f"{i}:{item}".encode()).hexdigest(), 16)
                if min_val is None or h < min_val:
                    min_val = h
            sig.append(min_val)
        return sig

    @staticmethod
    def _estimate_jaccard(sig_a: list, sig_b: list) -> float:
        matches = sum(1 for a, b in zip(sig_a, sig_b) if a == b)
        return matches / len(sig_a)

    @classmethod
    def _true_jaccard(cls, a: set, b: set) -> float:
        return len(a & b) / len(a | b)

    def produce(self) -> dict:
        """Compute estimated and true Jaccard similarity for the fixed sets and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({"tick": 0})

        sig_a = self._minhash_signature(self._SET_A)
        sig_b = self._minhash_signature(self._SET_B)
        estimated = self._estimate_jaccard(sig_a, sig_b)
        true = self._true_jaccard(self._SET_A, self._SET_B)

        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "estimated_jaccard": estimated,
            "true_jaccard": true,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
