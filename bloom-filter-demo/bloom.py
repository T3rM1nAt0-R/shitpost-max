import os
import json
import sys
from datetime import datetime, timezone
import hashlib
import secrets
import string
from harness.shitpost_base import Shitpost

BIT_COUNT = 1000

class BloomFilterDemo(Shitpost):
    """Bloom filter demo plugin."""

    name = "bloom-filter-demo"
    internal = False
    commit_template = "bloom-filter-demo: {bits_set}/{capacity} bits set, {fp_rate:.1%} false-positive rate"

    def __init__(self):
        super().__init__()
        self._state_file_name = "bloom_filter_state.json"

    def _bit_positions(self, item: str) -> list[int]:
        seeds = [b"s1", b"s2", b"s3"]
        return [
            int(hashlib.sha256(item.encode() + seed).hexdigest(), 16) % BIT_COUNT
            for seed in seeds
        ]

    def _add(self, bits: list, item: str) -> None:
        positions = self._bit_positions(item)
        for pos in positions:
            bits[pos] = 1

    def _might_contain(self, bits: list, item: str) -> bool:
        positions = self._bit_positions(item)
        return all(bits[pos] == 1 for pos in positions)

    def produce(self) -> dict:
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        bits = state["bits"]
        count = state["count"]
        tick = state["tick"]

        false_positives = 0

        for _ in range(50):
            item = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
            self._add(bits, item)
            count += 1

        for _ in range(100):
            item = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
            if self._might_contain(bits, item):
                false_positives += 1

        bits_set = sum(bits)
        fp_rate = false_positives / 100.0
        tick += 1

        state["bits"] = bits
        state["count"] = count
        state["tick"] = tick

        self._save_state(plugin_dir, state)

        return {
            "tick": tick,
            "bits_set": bits_set,
            "capacity": BIT_COUNT,
            "false_positives": false_positives,
            "probes": 100,
            "fp_rate": fp_rate
        }

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running Bloom filter state, or initialise it at F(0)."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: bloom filter state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"bits", "count", "tick"}
            if not required.issubset(state.keys()):
                print(
                    "warning: bloom filter state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            # The next number to emit is always ``a``; ``b`` is the one after.
            "bits": [0] * BIT_COUNT,
            "count": 0,
            "tick": 0,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)
