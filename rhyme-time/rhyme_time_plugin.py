"""Revolutionizing poetic composition with AI-enhanced phonetic pattern matching. Every perfect rhyme is a lyrical breakthrough."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class RhymeTimePlugin(Shitpost):
    """Emit one word and its known rhymes per tick from a fixed lookup table, cycling forever."""

    name = "rhyme-time"
    internal = False
    commit_template = "{word} rhymes with {rhymes}"

    _WORDS = ["cat", "light", "day", "tree", "code", "moon"]
    _RHYMES = {
        "cat": ["hat", "bat", "mat"],
        "light": ["night", "sight", "bright"],
        "day": ["way", "play", "say"],
        "tree": ["free", "sea", "key"],
        "code": ["road", "mode", "load"],
        "moon": ["soon", "tune", "spoon"],
    }

    def produce(self) -> dict:
        """Emit the next word/rhyme entry and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "word_index": 0,
            "tick": 0,
        })

        word = self._WORDS[state["word_index"] % len(self._WORDS)]
        rhymes = self._RHYMES[word]

        state["word_index"] = (state["word_index"] + 1) % len(self._WORDS)
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "word": word,
            "rhymes": rhymes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
