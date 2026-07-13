import random

def zipfian_keys(n: int, keyspace: int, s: float, seed: int) -> list[int]:
    rng = random.Random(seed)
    weights = [1 / (i + 1) ** s for i in range(keyspace)]
    return rng.choices(range(keyspace), weights=weights, k=n)
