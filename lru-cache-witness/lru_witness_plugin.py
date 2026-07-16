"""Built and stress-tested a production-grade LRU cache under adversarial access patterns. Hit rate: variable. Confidence: absolute."""

import os
import random
from collections import OrderedDict
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class LRUCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key):
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key, value) -> None:
        if key in self.cache:
            del self.cache[key]
        elif len(self.cache) >= self.capacity:
            self.cache.popitem(last=False)
        self.cache[key] = value

    def __len__(self):
        return len(self.cache)


def zipfian_keys(n: int, keyspace: int, s: float, seed: int) -> list[int]:
    rng = random.Random(seed)
    weights = [1 / (i + 1) ** s for i in range(keyspace)]
    return rng.choices(range(keyspace), weights=weights, k=n)


class LRUCacheWitnessPlugin(Shitpost):
    name = "lru-cache-witness"
    internal = False
    commit_template = "lru-cache-witness: {tick_hit_rate:.1%} this tick, {cumulative_hit_rate:.1%} overall — {cache_size} entries"

    def __init__(self):
        super().__init__()

    def produce(self) -> dict:
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state(default={"cumulative_hits": 0, "cumulative_misses": 0, "tick": 0})

        tick = state["tick"] + 1
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

        self._save_persisted_state(state)

        return {
            "tick": tick,
            "tick_hits": tick_hits,
            "tick_misses": tick_misses,
            "tick_hit_rate": tick_hit_rate,
            "cumulative_hits": cumulative_hits,
            "cumulative_misses": cumulative_misses,
            "cumulative_hit_rate": cumulative_hit_rate,
            "cache_size": len(cache),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
