"""Decentralized string storage infrastructure leveraging AI-optimized prefix trees. Every insertion is a node in the knowledge economy."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class TrieStatsPlugin(Shitpost):
    """Build a prefix trie incrementally, inserting one word per tick from a fixed cycling list."""

    name = "trie-stats"
    internal = False
    commit_template = "trie +{word}: {node_count} nodes, depth {max_depth}"

    _WORDS = ["cat", "car", "card", "dog", "do"]

    @staticmethod
    def _insert(root: dict, word: str) -> None:
        node = root
        for ch in word:
            node = node["children"].setdefault(ch, {"children": {}, "end": False})
        node["end"] = True

    @staticmethod
    def _count_nodes(node: dict) -> int:
        return sum(1 + TrieStatsPlugin._count_nodes(child) for child in node["children"].values())

    @staticmethod
    def _max_depth(node: dict, depth: int = 0) -> int:
        if not node["children"]:
            return depth
        return max(TrieStatsPlugin._max_depth(child, depth + 1) for child in node["children"].values())

    def produce(self) -> dict:
        """Insert the next word into the trie and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "trie": {"children": {}, "end": False},
            "word_index": 0,
            "tick": 0,
        })

        word = self._WORDS[state["word_index"] % len(self._WORDS)]
        self._insert(state["trie"], word)
        node_count = self._count_nodes(state["trie"])
        max_depth = self._max_depth(state["trie"])

        state["word_index"] += 1
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "word": word,
            "node_count": node_count,
            "max_depth": max_depth,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
