"""Revolutionizing maritime linguistic conversion with AI-enhanced golden-age-of-piracy translation. Every arrr is a cultural heritage preservation."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class PirateTranslatorPlugin(Shitpost):
    """Translate one fixed sentence into pirate-speak per tick, cycling forever."""

    name = "pirate-translator"
    internal = False
    commit_template = "pirate: {translated}"

    _SUBSTITUTIONS = {
        "my": "me", "hello": "ahoy", "friend": "matey", "yes": "aye",
        "you": "ye", "is": "be", "the": "th'",
    }
    _SENTENCES = [
        "Hello my friend",
        "Is the treasure here",
        "You are my friend",
        "Yes, hello there",
        "The map is real",
    ]

    @classmethod
    def _translate(cls, sentence: str) -> str:
        out = []
        for w in sentence.split():
            stripped = w.strip(",.")
            suffix = w[len(stripped):]
            lower = stripped.lower()
            if lower in cls._SUBSTITUTIONS:
                replacement = cls._SUBSTITUTIONS[lower]
                if stripped[:1].isupper():
                    replacement = replacement.capitalize()
                out.append(replacement + suffix)
            else:
                out.append(w)
        return " ".join(out)

    def produce(self) -> dict:
        """Translate the next fixed sentence and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "sentence_index": 0,
            "tick": 0,
        })

        original = self._SENTENCES[state["sentence_index"] % len(self._SENTENCES)]
        translated = self._translate(original)

        state["sentence_index"] = (state["sentence_index"] + 1) % len(self._SENTENCES)
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "original": original,
            "translated": translated,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
