"""AI-driven semantic softening platform for corporate communications compliance. Every euphemism is a PR crisis avoided."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class EuphemismEnginePlugin(Shitpost):
    """Emit one euphemistic phrase per tick from a fixed cycling lookup, softening a blunt phrase."""

    name = "euphemism-engine"
    internal = False
    commit_template = "euphemism: '{blunt}' -> '{euphemism}'"

    _PAIRS = [
        ("you're fired", "we're going in a different direction"),
        ("this is broken", "this has known limitations"),
        ("I don't know", "let me circle back on that"),
        ("we have no budget", "we're being resource-conscious"),
        ("this will take forever", "this is a multi-quarter initiative"),
        ("nobody uses this", "adoption is still ramping"),
    ]

    def produce(self) -> dict:
        """Emit the next euphemism pair and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "pair_index": 0,
            "tick": 0,
        })

        blunt, euphemism = self._PAIRS[state["pair_index"] % len(self._PAIRS)]

        state["pair_index"] = (state["pair_index"] + 1) % len(self._PAIRS)
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "blunt": blunt,
            "euphemism": euphemism,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
