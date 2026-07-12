import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class PascalRowPlugin(Shitpost):
    """Emit one row of Pascal's triangle per tick."""

    name = "pascal-row"
    internal = False
    commit_template = "pascal row {row_index}: {row}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "pascal_state.json"
        self._numbers_file_name = "pascal.txt"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running Pascal's triangle state, or initialise it at row 0."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: pascal state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"row", "row_index", "tick"}
            if not required.issubset(state.keys()):
                print(
                    "warning: pascal state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "row": [1],
            "row_index": 0,
            "tick": 0,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _append_number(self, plugin_dir: str, row: list) -> None:
        path = os.path.join(plugin_dir, self._numbers_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")

    def produce(self) -> dict:
        """Return the next row of Pascal's triangle and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Emit the current row.
        pascal_row = state["row"]
        row_index = state["row_index"]

        # Advance to the next row.
        if len(pascal_row) > 1:
            next_row = [1] + [pascal_row[i] + pascal_row[i+1] for i in range(len(pascal_row)-1)] + [1]
        else:
            next_row = [1, 1]

        state["row"] = next_row
        state["row_index"] += 1
        state["tick"] += 1

        self._save_state(plugin_dir, state)
        self._append_number(plugin_dir, pascal_row)

        return {
            "tick": state["tick"],
            "row_index": row_index,
            "row": pascal_row,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
