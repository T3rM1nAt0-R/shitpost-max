import json
import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class PascalRowPlugin(Shitpost):
    """Emit one row of Pascal's triangle per tick."""

    name = "pascal-row"
    internal = False
    commit_template = "pascal row {row_index}: {row}"

    def __init__(self):
        super().__init__()
        self._numbers_file_name = "pascal.txt"

    def _persisted_state_path(self) -> str:
        return os.path.join(self._plugin_dir(), "pascal_state.json")

    def _append_number(self, plugin_dir: str, row: list) -> None:
        path = os.path.join(plugin_dir, self._numbers_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")

    def produce(self) -> dict:
        """Return the next row of Pascal's triangle and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({"row": [1], "row_index": 0, "tick": 0})

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

        self._save_persisted_state(state)
        self._append_number(plugin_dir, pascal_row)

        return {
            "tick": state["tick"],
            "row_index": row_index,
            "row": pascal_row,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
