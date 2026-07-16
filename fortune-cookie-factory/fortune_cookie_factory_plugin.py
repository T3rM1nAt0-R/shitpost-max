"""Revolutionizing predictive text analytics with AI-optimized fortune cookie wisdom delivery. Every fortune is a personalized life insight."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class FortuneCookieFactoryPlugin(Shitpost):
    """Emit one fortune-cookie-style message per tick from a fixed cycling list."""

    name = "fortune-cookie-factory"
    internal = False
    commit_template = "fortune #{fortune_index}: {fortune}"

    _FORTUNES = [
        "A production incident is just a learning opportunity in disguise.",
        "The bug you cannot reproduce will find you at 3am.",
        "Your next commit message will be more honest than you intend.",
        "A wise engineer reads the error message before Googling it.",
        "The cache you forgot to invalidate remembers everything.",
        "Today's technical debt is tomorrow's team-building exercise.",
    ]

    def produce(self) -> dict:
        """Emit the next fortune and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "fortune_index": 0,
            "tick": 0,
        })

        fortune_index = state["fortune_index"] % len(self._FORTUNES)
        fortune = self._FORTUNES[fortune_index]

        state["fortune_index"] = (state["fortune_index"] + 1) % len(self._FORTUNES)
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "fortune_index": fortune_index,
            "fortune": fortune,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
