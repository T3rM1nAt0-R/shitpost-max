import json
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
        self._state_file_name = "buzzwords_state.json"
        self._buzzwords_file_name = "buzzwords.txt"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running buzzword state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: buzzword state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"last_generated": "0"}
            if not required.issubset(state.keys()):
                print(
                    "warning: buzzword state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "last_generated": "0",
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

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
        with open(self._plugin_dir() + "/" + self._buzzwords_file_name, 'r') as file:
            for line in file:
                if buzzword in line:
                    return False
        return True

    def produce(self) -> dict:
        """Return the next unique Silicon Valley buzzword and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        buzzword = self._generate_buzzword()
        while not self._is_unique(buzzword):
            buzzword = self._generate_buzzword()

        state["last_generated"] = str(datetime.now(timezone.utc).timestamp())

        self._save_state(plugin_dir, state)
        self._append_buzzword(plugin_dir, buzzword)

        return {
            "tick": int(state["last_generated"]),
            "buzzword": buzzword,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
