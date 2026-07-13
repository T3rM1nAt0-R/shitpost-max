import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from harness.shitpost_base import Shitpost


class MetaPlugin(Shitpost):
    """Generate a daily status report for all sibling projects."""

    name = "shitpost-max-meta"
    internal = True
    commit_template = "meta: daily status report {date}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "status_report_state.json"
        self._report_file_name = "status-report.md"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: status report state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"last_commit": "1970-01-01T00:00:00+00:00"}
            if not required.issubset(state.keys()):
                print(
                    "warning: status report state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "last_commit": "1970-01-01T00:00:00+00:00",
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _generate_report(self, plugin_dir: str) -> None:
        path = os.path.join(plugin_dir, self._report_file_name)
        with open(path, "w", encoding="utf-8") as f:
            f.write("# Status Report\n\n")
            f.write("| Repository | Commit Hash | Timestamp | Message |\n")
            f.write("|------------|-------------|-----------|---------|\n")

    def produce(self) -> dict:
        """Generate the status report and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Generate the status report
        self._generate_report(plugin_dir)

        # Update the state with the current timestamp
        state["last_commit"] = datetime.now(timezone.utc).isoformat()

        self._save_state(plugin_dir, state)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
