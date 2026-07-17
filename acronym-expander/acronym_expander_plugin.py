"""Pioneering recursive acronym expansion through AI-driven initialism interpretation. Every backronym is a brand identity waiting to happen."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class AcronymExpanderPlugin(Shitpost):
    """Emit one humorous backronym expansion per tick from a fixed cycling list."""

    name = "acronym-expander"
    internal = False
    commit_template = "{acronym} = {expansion}"

    _PAIRS = [
        ("CI/CD", "Constantly Interrupted, Continuously Dreading"),
        ("API", "Another Pointless Integration"),
        ("SDK", "Suspiciously Difficult Kit"),
        ("MVP", "Mostly Vaporware, Probably"),
        ("KPI", "Keeps Panicking Indefinitely"),
        ("ROI", "Reasoning Over It, eventually"),
    ]

    def produce(self) -> dict:
        """Emit the next acronym expansion and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "pair_index": 0,
            "tick": 0,
        })

        acronym, expansion = self._PAIRS[state["pair_index"] % len(self._PAIRS)]

        state["pair_index"] = (state["pair_index"] + 1) % len(self._PAIRS)
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "acronym": acronym,
            "expansion": expansion,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
