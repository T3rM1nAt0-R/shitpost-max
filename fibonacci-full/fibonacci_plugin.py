"""Rebuilt nature's favorite sequence as a microservice. One full Fibonacci number per tick — rabbits optional.

Uses Python's arbitrary-precision integers so the sequence never
overflows or truncates.  The running state is persisted in
``fibonacci_state.json`` so each tick resumes where the previous one
left off, and every emitted number is appended to ``fibonacci.txt``.
"""

import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost, summarize_big_int


class FibonacciPlugin(Shitpost):
    """Emit one full Fibonacci number per tick."""

    name = "fibonacci-full"
    internal = False
    commit_template = "fibonacci F({n}): {fibonacci}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "fibonacci_state.json"
        self._numbers_file_name = "fibonacci.txt"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running Fibonacci state, or initialise it at F(0)."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: fibonacci state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"a", "b", "n", "tick"}
            if not required.issubset(state.keys()):
                print(
                    "warning: fibonacci state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            # The next number to emit is always ``a``; ``b`` is the one after.
            "a": 0,
            "b": 1,
            "n": 0,
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
        """Return the next Fibonacci number and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Emit the next number, then advance the pair.
        fib = state["a"]
        state["a"], state["b"] = state["b"], state["a"] + state["b"]
        state["tick"] += 1

        n = state["n"]
        state["n"] += 1

        self._save_state(plugin_dir, state)
        self._append_number(plugin_dir, fib)

        return {
            "tick": state["tick"],
            "n": n,
            "fibonacci": summarize_big_int(fib),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
