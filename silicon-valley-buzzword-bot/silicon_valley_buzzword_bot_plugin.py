"""Generates one novel Silicon Valley buzzword per tick, feeding the exact ecosystem this joke repo is making fun of."""

import os
import random
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class SiliconValleyBuzzwordBotPlugin(Shitpost):
    """Generate one novel Silicon Valley buzzword per tick."""

    name = "silicon-valley-buzzword-bot"
    internal = False
    commit_template = "buzzword: {buzzword}"

    def __init__(self):
        super().__init__()
        self._buzzwords_file_name = "buzzwords.txt"

    def _persisted_state_path(self) -> str:
        return os.path.join(self._plugin_dir(), "buzzwords_state.json")

    def _append_buzzword(self, plugin_dir: str, buzzword: str) -> None:
        path = os.path.join(plugin_dir, self._buzzwords_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{buzzword} — {datetime.now(timezone.utc).isoformat()}\n")

    def _generate_buzzword(self) -> str:
        prefixes = ["Giga", "Hyper", "Inno", "Next"]
        roots = ["Wave", "Revolution", "Breakthrough", "Shift"]
        suffixes = ["Tech", "Venture", "Innovation", "Future"]

        buzzword = f"{random.choice(prefixes)}{random.choice(roots)}{random.choice(suffixes)}"
        return buzzword

    def _is_unique(self, buzzword: str) -> bool:
        path = os.path.join(self._plugin_dir(), self._buzzwords_file_name)
        if not os.path.exists(path):
            return True
        with open(path, 'r') as file:
            for line in file:
                if buzzword in line:
                    return False
        return True

    def produce(self) -> dict:
        """Return the next unique Silicon Valley buzzword and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({"last_generated": "0"})

        # Only 4 prefixes x 4 roots x 4 suffixes = 64 possible buzzwords
        # exist, and buzzwords.txt never prunes old entries -- so once all
        # 64 have been seen, this used to spin forever looking for a "new"
        # one that could never exist (confirmed in production on
        # 2026-07-14: pegged 8 CPU cores for 5+ hours and starved every
        # other plugin's tick behind it). Bound the search and start a
        # fresh cycle instead of hanging once the vocabulary is exhausted.
        buzzword = self._generate_buzzword()
        attempts = 1
        while not self._is_unique(buzzword) and attempts < 200:
            buzzword = self._generate_buzzword()
            attempts += 1
        if not self._is_unique(buzzword):
            path = os.path.join(plugin_dir, self._buzzwords_file_name)
            if os.path.exists(path):
                os.remove(path)

        state["last_generated"] = str(datetime.now(timezone.utc).timestamp())

        self._save_persisted_state(state)
        self._append_buzzword(plugin_dir, buzzword)

        return {
            "tick": int(float(state["last_generated"])),
            "buzzword": buzzword,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
