import json
import os
import sys
from datetime import datetime, timezone
import tempfile

from harness.shitpost_base import Shitpost


class CollatzExplorerPlugin(Shitpost):
    """Explore the Collatz stopping time for each integer n."""

    name = "collatz-explorer"
    internal = False
    commit_template = "collatz record: n={n} took {steps} steps"

    def __init__(self):
        super().__init__()
        self._state_file_name = "collatz_state.json"
        self._records_file_name = "records.txt"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running collatz state, or initialise it for the first tick."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: collatz state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            required = {
                "current_n",
                "max_steps",
                "tick",
            }
            if not required.issubset(state.keys()):
                print(
                    "warning: collatz state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        # Start with current_n=1, max_steps=-1 (no record yet), and tick=0
        return {
            "current_n": 1,
            "max_steps": -1,
            "tick": 0,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _append_record(self, plugin_dir: str, n: int, steps: int) -> None:
        path = os.path.join(plugin_dir, self._records_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"n={n} steps={steps}\n")

    def _collatz_stopping_time(self, n: int) -> int:
        """Compute the Collatz stopping time for a given integer n."""
        steps = 0
        while n != 1:
            if n % 2 == 0:
                n //= 2
            else:
                n = 3 * n + 1
            steps += 1
        return steps

    def produce(self) -> dict | None:
        """Return the Collatz stopping time for current_n and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        n = state["current_n"]
        steps = self._collatz_stopping_time(n)

        if steps > state["max_steps"]:
            state["max_steps"] = steps
            self._append_record(plugin_dir, n, steps)
            commit_message = self.commit_template.format(n=n, steps=steps)
        else:
            commit_message = None

        state["current_n"] += 1
        state["tick"] += 1
        self._save_state(plugin_dir, state)

        return {
            "tick": state["tick"],
            "n": n,
            "steps": steps,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        } if commit_message else None
