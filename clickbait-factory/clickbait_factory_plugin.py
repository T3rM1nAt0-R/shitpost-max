"""Revolutionizing viral content creation with AI-optimized click-through maximization. Every headline is an engagement growth hack."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class ClickbaitFactoryPlugin(Shitpost):
    """Emit one fully-filled clickbait headline per tick from a fixed cycling list."""

    name = "clickbait-factory"
    internal = False
    commit_template = "clickbait #{headline_index}: {headline}"

    _HEADLINES = [
        "You Won't Believe What This Cron Job Does Every 30 Seconds",
        "7 Shocking Facts About Pi That Mathematicians Don't Want You To Know",
        "This One Weird Trick Makes Your Git History Green Forever",
        "Local Engineer Discovers The Last Digit Of Pi, Investors Are Furious",
        "Doctors Hate Him: One Scheduler Ticks 88 Times A Day",
        "What Happens When You Commit Every Second Will Astonish You",
    ]

    def produce(self) -> dict:
        """Emit the next clickbait headline and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "headline_index": 0,
            "tick": 0,
        })

        headline_index = state["headline_index"] % len(self._HEADLINES)
        headline = self._HEADLINES[headline_index]

        state["headline_index"] = (state["headline_index"] + 1) % len(self._HEADLINES)
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "headline_index": headline_index,
            "headline": headline,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
