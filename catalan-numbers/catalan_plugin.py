import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class CatalanNumbersPlugin(Shitpost):
    """Emit one full Catalan number per tick."""

    name = "catalan-numbers"
    internal = False
    commit_template = "catalan C({n}): {catalan}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "catalan_state.json"
        self._numbers_file_name = "catalan.txt"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running Catalan state, or initialise it at C(0)."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: catalan state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"n", "current_catalan", "tick"}
            if not required.issubset(state.keys()):
                print(
                    "warning: catalan state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            # The next number to emit is always ``current_catalan``.
            "n": 0,
            "current_catalan": 1,
            "tick": 0,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _append_number(self, plugin_dir: str, number: int) -> None:
        path = os.path.join(plugin_dir, self._numbers_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(str(number) + "\n")

    def produce(self) -> dict:
        """Return the next Catalan number and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Emit the current catalan number.
        catalan = state["current_catalan"]
        n = state["n"]

        # Advance to the next catalan number using the recurrence relation.
        if n > 0:
            state["current_catalan"] = (state["current_catalan"] * 2 * (2 * n + 1)) // (n + 2)

        state["tick"] += 1
        state["n"] += 1

        self._save_state(plugin_dir, state)
        self._append_number(plugin_dir, catalan)

        return {
            "tick": state["tick"],
            "n": n,
            "catalan": catalan,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
