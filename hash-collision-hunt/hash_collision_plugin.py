import json
import os
import random
import sys
import string
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


def weak_hash(s: str) -> int:
    """Weak hash function that sums the byte values of the input string modulo 256."""
    return sum(s.encode()) % 256


class HashCollisionHuntPlugin(Shitpost):
    """Hash collision hunt plugin."""

    name = "hash-collision-hunt"
    internal = False
    commit_template = "hash-collision-hunt: {total_hashes} hashes, {collisions_found} collisions, table {fill_ratio:.0%} full"

    def __init__(self):
        super().__init__()
        self._state_file_name = "hash_collision_state.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: hash collision state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"total_hashes", "collisions_found", "collision_table", "tick"}
            if not required.issubset(state.keys()):
                print(
                    "warning: hash collision state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "total_hashes": 0,
            "collisions_found": 0,
            "collision_table": {},
            "tick": 0,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def produce(self) -> dict:
        """Generate random strings and check for hash collisions."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        latest_collision = None
        for _ in range(10000):
            s = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            h = weak_hash(s)
            hash_byte_str = str(h)
            if hash_byte_str in state["collision_table"] and state["collision_table"][hash_byte_str] != s:
                latest_collision = {
                    "hash_byte": hash_byte_str,
                    "input_a": state["collision_table"][hash_byte_str],
                    "input_b": s
                }
                state["collisions_found"] += 1
            if hash_byte_str not in state["collision_table"]:
                state["collision_table"][hash_byte_str] = s

        state["total_hashes"] += 10000
        state["tick"] += 1

        fill_ratio = len(state["collision_table"]) / 256.0
        self._save_state(plugin_dir, state)

        return {
            "tick": state["tick"],
            "total_hashes": state["total_hashes"],
            "collisions_found": state["collisions_found"],
            "fill_ratio": fill_ratio,
            "latest_collision": latest_collision
        }


