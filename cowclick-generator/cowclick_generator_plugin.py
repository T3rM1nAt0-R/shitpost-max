"""Pioneering AI-enhanced bovine communication through ASCII art rendering pipelines. Every cow is a text-to-visual paradigm shift."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class CowclickGeneratorPlugin(Shitpost):
    """Emit one cowsay-style ASCII speech bubble per tick, wrapping a fixed cycling message."""

    name = "cowclick-generator"
    internal = False
    commit_template = "cowclick: {message}"

    _MESSAGES = [
        "ship it",
        "works on my machine",
        "it's a feature",
        "just one more commit",
        "green means go",
    ]

    @staticmethod
    def _cow_art(message: str) -> str:
        border = "-" * (len(message) + 2)
        return (
            f" {border}\n"
            f"< {message} >\n"
            f" {border}\n"
            "        \\   ^__^\n"
            "         \\  (oo)\\_______\n"
            "            (__)\\       )\\/\\\n"
            "                ||----w |\n"
            "                ||     ||"
        )

    def produce(self) -> dict:
        """Emit the next cow-art message and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "message_index": 0,
            "tick": 0,
        })

        message = self._MESSAGES[state["message_index"] % len(self._MESSAGES)]
        art = self._cow_art(message)

        state["message_index"] = (state["message_index"] + 1) % len(self._MESSAGES)
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "message": message,
            "art": art,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
