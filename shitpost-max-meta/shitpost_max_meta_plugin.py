import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class MetaPlugin(Shitpost):
    """Generate a daily status report for all sibling projects."""

    name = "shitpost-max-meta"
    internal = True
    commit_template = "meta: daily status report {timestamp}"

    def __init__(self):
        super().__init__()
        self._report_file_name = "status-report.md"

    def _persisted_state_path(self) -> str:
        return os.path.join(self._plugin_dir(), "status_report_state.json")

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

        state = self._load_persisted_state(
            {"last_commit": "1970-01-01T00:00:00+00:00"}
        )

        # Generate the status report
        self._generate_report(plugin_dir)

        # Update the state with the current timestamp
        state["last_commit"] = datetime.now(timezone.utc).isoformat()

        self._save_persisted_state(state)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
