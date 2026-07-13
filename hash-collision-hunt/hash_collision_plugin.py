import os
import random
import string

from harness.shitpost_base import Shitpost


def weak_hash(s: str) -> int:
    """Weak hash function that sums the byte values of the input string modulo 256."""
    return sum(s.encode()) % 256


class HashCollisionHuntPlugin(Shitpost):
    """Hash collision hunt plugin."""

    name = "hash-collision-hunt"
    internal = False
    commit_template = "hash-collision-hunt: {total_hashes} hashes, {collisions_found} collisions, table {fill_ratio:.0%} full"

    def _persisted_state_path(self) -> str:
        return os.path.join(self._plugin_dir(), "hash_collision_state.json")

    def produce(self) -> dict:
        """Generate random strings and check for hash collisions."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "total_hashes": 0,
            "collisions_found": 0,
            "collision_table": {},
            "tick": 0,
        })

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
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "total_hashes": state["total_hashes"],
            "collisions_found": state["collisions_found"],
            "fill_ratio": fill_ratio,
            "latest_collision": latest_collision
        }


