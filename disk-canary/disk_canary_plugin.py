import json
import os
import sys
from datetime import datetime, timezone
import psutil

from harness.shitpost_base import Shitpost


class DiskCanaryPlugin(Shitpost):
    """Monitor disk usage for configured mounts."""

    name = "disk-canary"
    internal = True
    commit_template = "disk: / {root_pct}%, /mnt/data {data_pct}%"

    def __init__(self):
        super().__init__()
        self._state_file_name = "disk_summary.json"
        self._log_file_name = "disk_log.jsonl"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running disk usage state."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: disk usage state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return {}
        else:
            return {}

        return state

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _append_log(self, plugin_dir: str, log_entry: dict) -> None:
        path = os.path.join(plugin_dir, self._log_file_name)
        with open(path, "a", encoding="utf-8") as f:
            json.dump(log_entry, f)
            f.write("\n")

    def produce(self) -> dict | None:
        """Return the current disk usage and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        mounts = ["/", "/mnt/data"]
        for mount in mounts:
            usage = psutil.disk_usage(mount)
            log_entry = {
                "mount": mount,
                "total_bytes": usage.total,
                "free_bytes": usage.free,
                "used_bytes": usage.used,
                "used_percent": usage.percent,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._append_log(plugin_dir, log_entry)

            if mount not in state or state[mount]["used_percent"] != usage.percent:
                state[mount] = {
                    "total_bytes": usage.total,
                    "free_bytes": usage.free,
                    "used_bytes": usage.used,
                    "used_percent": usage.percent,
                }

        self._save_state(plugin_dir, state)

        root_state = state.get("/", {})
        data_state = state.get("/mnt/data", {})
        return {
            **state,
            "root_pct": root_state.get("used_percent", 0),
            "data_pct": data_state.get("used_percent", 0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
