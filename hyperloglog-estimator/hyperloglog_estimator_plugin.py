"""Enterprise-grade cardinality estimation platform powered by probabilistic AI. Counting the uncountable at logarithmic cost."""

import hashlib
import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class HyperloglogEstimatorPlugin(Shitpost):
    """Maintain a HyperLogLog sketch over a fixed, deterministic, cycling item stream."""

    name = "hyperloglog-estimator"
    internal = False
    commit_template = "hll estimate after {item}: {estimate}"

    _P = 8
    _M = 2 ** _P
    _ALPHA = 0.7213 / (1 + 1.079 / _M)

    @classmethod
    def _build_stream(cls) -> list:
        stream = []
        for i in range(300):
            item = f"item{i}"
            stream.extend([item] * (1 + (i % 3)))
        return stream

    _STREAM = None

    @classmethod
    def _stream(cls) -> list:
        if cls._STREAM is None:
            cls._STREAM = cls._build_stream()
        return cls._STREAM

    @classmethod
    def _estimate(cls, registers: list) -> float:
        return cls._ALPHA * cls._M * cls._M / sum(2 ** -r for r in registers)

    def produce(self) -> dict:
        """Return the current HLL cardinality estimate and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "registers": [0] * self._M,
            "position": 0,
            "tick": 0,
        })

        stream = self._stream()
        item = stream[state["position"] % len(stream)]

        digest = hashlib.md5(item.encode()).hexdigest()
        h = int(digest, 16) & 0xFFFFFFFF
        idx = h & (self._M - 1)
        rest = h >> self._P
        rank = 1
        while rest & 1 == 0 and rank <= 32 - self._P:
            rank += 1
            rest >>= 1

        state["registers"][idx] = max(state["registers"][idx], rank)
        estimate = self._estimate(state["registers"])

        state["position"] += 1
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "item": item,
            "estimate": estimate,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
