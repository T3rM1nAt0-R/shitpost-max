"""Disrupting the placeholder text industry with AI-powered classical Latin dummy content delivery. Every word is a typographic layout asset."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class LoremIpsumStreamPlugin(Shitpost):
    """Emit one word of the standard Lorem Ipsum passage per tick, cycling forever."""

    name = "lorem-ipsum-stream"
    internal = False
    commit_template = "lorem ipsum word #{word_index}: {word}"

    _PASSAGE = (
        "Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod "
        "tempor incididunt ut labore et dolore magna aliqua"
    )
    _WORDS = _PASSAGE.split()

    def produce(self) -> dict:
        """Emit the next Lorem Ipsum word and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "word_index": 0,
            "tick": 0,
        })

        word_index = state["word_index"] % len(self._WORDS)
        word = self._WORDS[word_index]

        state["word_index"] = (state["word_index"] + 1) % len(self._WORDS)
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "word_index": word_index,
            "word": word,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
