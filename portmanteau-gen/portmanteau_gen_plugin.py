"""AI-constrained lexical fusion engine for neologism generation. Every portmanteau is a brand synergy waiting to happen."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class PortmanteauGenPlugin(Shitpost):
    """Emit one portmanteau blend per tick from a fixed cycling list of triples."""

    name = "portmanteau-gen"
    internal = False
    commit_template = "{word1} + {word2} = {blend}"

    _TRIPLES = [
        ("breakfast", "lunch", "brunch"),
        ("smoke", "fog", "smog"),
        ("spoon", "fork", "spork"),
        ("motor", "hotel", "motel"),
        ("email", "internet", "einternet"),
        ("chill", "relax", "chillax"),
    ]

    def produce(self) -> dict:
        """Emit the next portmanteau triple and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "triple_index": 0,
            "tick": 0,
        })

        word1, word2, blend = self._TRIPLES[state["triple_index"] % len(self._TRIPLES)]

        state["triple_index"] = (state["triple_index"] + 1) % len(self._TRIPLES)
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "word1": word1,
            "word2": word2,
            "blend": blend,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
