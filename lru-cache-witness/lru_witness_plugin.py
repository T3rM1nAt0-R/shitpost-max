import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost
from workload import zipfian_keys
from lru_cache import LRUCache

class LRUCacheWitnessPlugin(Shitpost):
    name = "lru-cache-witness"
    internal = False
    commit_template = "lru-cache-witness: {tick_hit_rate:.1%} this tick, {cumulative_hit_rate:.1%} overall — {cache_size} entries"

    def __init__(self):
        super().__init__()
        self._state_file_name = "lru_cache_witness_state.json"

    def _load_state(self, plugin_dir: str) -> dict:
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: lru-cache-witness state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            required = {"cumulative_hits", "cumulative_misses", "tick"}
            if not required.issubset(state.keys()):
                print(
                    "warning: lru-cache-witness state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "cumulative_hits": 0,
            "cumulative_misses": 0,
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
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        tick = state["tick"]
        tick += 1
        state["tick"] = tick

        cache = LRUCache(capacity=100)
        keys = zipfian_keys(1000, 1000, 1.5, seed=tick)
        tick_hits = 0
        tick_misses = 0

        for key in keys:
            value = cache.get(key)
            if value is None:
                cache.put(key, key)
                tick_misses += 1
            else:
                tick_hits += 1

        cumulative_hits = state["cumulative_hits"] + tick_hits
        cumulative_misses = state["cumulative_misses"] + tick_misses
        tick_hit_rate = tick_hits / (tick_hits + tick_misses) if tick_hits + tick_misses > 0 else 0
        cumulative_hit_rate = cumulative_hits / (cumulative_hits + cumulative_misses) if cumulative_hits + cumulative_misses > 0 else 0

        state["cumulative_hits"] = cumulative_hits
        state["cumulative_misses"] = cumulative_misses

        self._save_state(plugin_dir, state)

        return {
            "tick": tick,
            "tick_hits": tick_hits,
            "tick_misses": tick_misses,
            "tick_hit_rate": tick_hit_rate,
            "cumulative_hits": cumulative_hits,
            "cumulative_misses": cumulative_misses,
            "cumulative_hit_rate": cumulative_hit_rate,
            "cache_size": len(cache),
        }
