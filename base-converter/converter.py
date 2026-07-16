"""Built a universal number-base translation layer. Counts up, converts bases, ships a commit — full-stack numeral literacy.

Maintains a growing integer that increments by 1 each tick. Each tick, converts the integer
to a new base (2 through 36, cycling). Logs the integer, base, and representation per tick.
"""

import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"


class BaseConverterPlugin(Shitpost):
    """Increment a persistent counter and convert it to a new base each tick."""

    name = "base-converter"
    internal = False
    commit_template = "base-converter: {value} in base {base} = {representation}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "counter.json"

    def _load_state(self, plugin_dir: str) -> int:
        """Load the counter state, or initialize it to 0."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)["value"]
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                print(
                    f"warning: counter state file is corrupt ({exc}); starting from 0",
                    file=sys.stderr,
                )
                return 0
        return 0

    def _save_state(self, plugin_dir: str, value: int) -> None:
        """Persist the counter atomically using a temp file and os.replace."""
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump({"value": value}, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    @staticmethod
    def to_base(n: int, base: int) -> str:
        """Convert a non-negative integer to a string in the given base.

        Supports bases 2 through 36 using lowercase alphanumerics.
        """
        if base < 2 or base > 36:
            raise ValueError("Base must be between 2 and 36")
        if n < 0:
            raise ValueError("Only non-negative integers are supported")
        if n == 0:
            return "0"

        result = []
        while n > 0:
            n, remainder = divmod(n, base)
            result.append(ALPHABET[remainder])
        return "".join(reversed(result))

    def produce(self) -> dict:
        """Return the next representation of the counter in a new base."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        value = state + 1
        tick_number = value - 1  # 0-indexed call count
        base = (tick_number % 35) + 2
        representation = self.to_base(value, base)

        self._save_state(plugin_dir, value)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tick_number": tick_number,
            "value": value,
            "base": base,
            "representation": representation,
        }
