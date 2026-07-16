"""Turned a 17th-century triangle into a tick-based data pipeline. One row per tick — binomial coefficients as a service."""

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

    @staticmethod
    def _row_for_logging(row: list) -> list | dict:
        """Return the row as-is while it's small, else a bounded summary.

        Pascal's triangle rows grow exponentially in digit-length forever,
        but this value is force-committed into state.jsonl (and the commit
        message itself) every single tick -- unbounded, forever. Left
        unchecked, that's exactly what grew pascal-row/state.jsonl to
        164MB and silently broke every push since GitHub's 100MB
        per-file limit was crossed (~1142 ticks in, discovered 2026-07-16).
        The full, untruncated row is still appended in full to
        ``pascal.txt`` via ``_append_number`` above -- nothing is lost,
        this only bounds what git is asked to store forever per tick.
        """
        serialized = json.dumps(row)
        if len(serialized) <= 2000:
            return row
        return {
            "row_length": len(row),
            "max_value_digit_count": len(str(max(row))),
            "first_3": row[:3],
            "last_3": row[-3:],
            "truncated": True,
        }

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
            "row": self._row_for_logging(pascal_row),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
