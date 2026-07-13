import json
import os
import random
from datetime import datetime, timezone
from typing import List, Tuple

import math
import sys

from harness.shitpost_base import Shitpost

RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
SUITS = ["hearts", "diamonds", "clubs", "spades"]
DECK = [(r, s) for s in SUITS for r in RANKS]

def fisher_yates_shuffle(deck: List[Tuple[str, str]], rng: random.Random) -> List[Tuple[str, str]]:
    d = list(deck)
    for i in range(len(d) - 1, 0, -1):
        j = rng.randint(0, i)
        d[i], d[j] = d[j], d[i]
    return d

def overhand_shuffle(deck: List[Tuple[str, str]], rng: random.Random) -> List[Tuple[str, str]]:
    d = list(deck)
    blocks = []
    while d:
        block_size = rng.randint(1, 10)
        blocks.append(d[:block_size])
        d = d[block_size:]
    result = []
    for b in reversed(blocks):
        result.extend(b)
    return result

def naive_swap_shuffle(deck: List[Tuple[str, str]], rng: random.Random, n_swaps: int) -> List[Tuple[str, str]]:
    d = list(deck)
    for _ in range(n_swaps):
        i, j = rng.randint(0, len(d) - 1), rng.randint(0, len(d) - 1)
        d[i], d[j] = d[j], d[i]
    return d

ALGOS = [
    ("fisher_yates", lambda deck, rng: fisher_yates_shuffle(deck, rng)),
    ("overhand", lambda deck, rng: overhand_shuffle(deck, rng)),
    ("naive_swap", lambda deck, rng: naive_swap_shuffle(deck, rng, 52))
]

def shannon_entropy(permutation_signatures: List[str]) -> float:
    if not permutation_signatures:
        return 0.0
    from collections import Counter
    counts = Counter(permutation_signatures)
    total = sum(counts.values())
    entropy = -sum(count / total * math.log2(count / total) for count in counts.values())
    return entropy

class CardShufflerPlugin(Shitpost):
    """Shuffle a deck of cards using different algorithms and track entropy."""

    name = "card-shuffler"
    internal = False
    commit_template = "shuffle: {algorithm} — entropy {entropy:.4f}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "card_shuffler_state.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it at tick 0."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: card-shuffler state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"tick", "algo_index", "recent_signatures", "total_shuffles", "algorithm_counts"}
            if not required.issubset(state.keys()):
                print(
                    "warning: card-shuffler state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "tick": 0,
            "algo_index": 0,
            "recent_signatures": [],
            "total_shuffles": 0,
            "algorithm_counts": {}
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def produce(self) -> dict:
        """Return the next shuffled deck and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        rng = random.Random()
        naive_swaps = int(os.environ.get("NAIVE_SWAPS", 52))
        algos = [
            ("fisher_yates", lambda deck, rng: fisher_yates_shuffle(deck, rng)),
            ("overhand", lambda deck, rng: overhand_shuffle(deck, rng)),
            ("naive_swap", lambda deck, rng: naive_swap_shuffle(deck, rng, naive_swaps)),
        ]
        forced_algo = os.environ.get("SHUFFLE_ALGO", "").strip()
        valid_names = [a[0] for a in algos]
        if forced_algo in valid_names:
            name, func = next(a for a in algos if a[0] == forced_algo)
        else:
            name, func = algos[state["algo_index"] % 3]
        result = func(DECK, rng)

        signature = str(tuple(result))
        state["recent_signatures"].append(signature)
        state["recent_signatures"] = state["recent_signatures"][-20:]

        entropy = shannon_entropy(state["recent_signatures"])

        state["total_shuffles"] += 1
        state["algorithm_counts"][name] = state["algorithm_counts"].get(name, 0) + 1
        state.setdefault("entropy_sums", {})
        state["entropy_sums"][name] = state["entropy_sums"].get(name, 0.0) + entropy

        state["algo_index"] += 1
        state["tick"] += 1

        self._save_state(plugin_dir, state)

        avg_entropy_per_algorithm = {
            algo: state["entropy_sums"][algo] / state["algorithm_counts"][algo]
            for algo in state["algorithm_counts"]
        }
        stats_path = os.path.join(plugin_dir, "shuffle_stats.json")
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "total_shuffles": state["total_shuffles"],
                    "algorithm_counts": state["algorithm_counts"],
                    "avg_entropy_per_algorithm": avg_entropy_per_algorithm,
                },
                f,
                separators=(",", ":"),
                sort_keys=True,
            )
            f.write("\n")

        return {
            "tick": state["tick"],
            "algorithm": name,
            "entropy": entropy,
            "deck_order": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
