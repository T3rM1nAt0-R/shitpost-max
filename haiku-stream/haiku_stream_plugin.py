"""Revolutionizing Japanese poetic form generation with AI-enhanced 5-7-5 syllable optimization. Every haiku is a literary NFT."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class HaikuStreamPlugin(Shitpost):
    """Emit one pre-written haiku per tick from a fixed cycling list."""

    name = "haiku-stream"
    internal = False
    commit_template = "haiku #{haiku_index}"

    _HAIKUS = [
        ["Servers hum all night", "Commits pile up like fresh snow", "Dawn deploy, no bugs"],
        ["The scheduler ticks", "Eighty-eight tiny cron jobs", "None of them matter"],
        ["Green squares on my graph", "A calendar made of lies", "Still counts as progress"],
        ["Pi digit found here", "One more decimal closer", "Never quite arrives"],
        ["Fork the repo, friend", "Stars do not pay the server bill", "Ship it anyway"],
    ]

    def produce(self) -> dict:
        """Emit the next haiku and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "haiku_index": 0,
            "tick": 0,
        })

        haiku_index = state["haiku_index"] % len(self._HAIKUS)
        haiku = "\n".join(self._HAIKUS[haiku_index])

        state["haiku_index"] = (state["haiku_index"] + 1) % len(self._HAIKUS)
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "haiku_index": haiku_index,
            "haiku": haiku,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
