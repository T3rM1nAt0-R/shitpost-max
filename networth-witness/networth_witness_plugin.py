import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class NetWorthWitnessPlugin(Shitpost):
    """Log a manually-entered net-worth number each tick and chart the trend over time."""

    name = "networth-witness"
    internal = False
    commit_template = "networth: {networth} ({count} entries)"

    def __init__(self):
        super().__init__()
        self._state_file_name = "state.jsonl"

    def _load_state(self, plugin_dir: str) -> list:
        """Load the running net-worth state, or initialise it as an empty list."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = [json.loads(line) for line in f]
            except json.JSONDecodeError as exc:
                print(
                    f"warning: networth state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return []
            # Guard against manual tampering / old versions.
            required = {"timestamp", "networth"}
            if not all(required.issubset(item.keys()) for item in state):
                print(
                    "warning: networth state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return []
            return state

        return []

    def _save_state(self, plugin_dir: str, state: list) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            for item in state:
                json.dump(item, f)
                f.write("\n")
        os.replace(tmp_path, path)

    def produce(self) -> dict | None:
        """Return the next net-worth entry and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Get NETWORTH from environment
        networth = os.getenv("NETWORTH")
        if not networth:
            print("warning: NETWORTH is unset; skipping tick", file=sys.stderr)
            return None

        timestamp = datetime.now(timezone.utc).isoformat()
        note = os.getenv("NOTE")  # Optional note from environment
        entry = {"timestamp": timestamp, "networth": int(networth), "note": note}

        state.append(entry)

        self._save_state(plugin_dir, state)

        return {
            "tick": len(state),
            "networth": int(networth),
            "count": len(state),
            "timestamp": timestamp,
        }
