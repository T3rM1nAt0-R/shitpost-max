import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class RamWitnessPlugin(Shitpost):
    """Memory-pressure logger for the i7 host."""

    name = "ram-witness"
    internal = True
    commit_template = "ram: {percent}% used ({used_gb}GB / {total_gb}GB)"

    def __init__(self):
        super().__init__()
        self._state_file_name = "ram_log.jsonl"
        self._summary_file_name = "ram_summary.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running RAM state."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: ram log file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"timestamp", "total_gb", "used_gb", "available_gb", "percent"}
            if not required.issubset(state.keys()):
                print(
                    "warning: ram log missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "timestamp": None,
            "total_gb": 0,
            "used_gb": 0,
            "available_gb": 0,
            "percent": 0.0,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _append_summary(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._summary_file_name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)

    def produce(self) -> dict:
        """Return the current RAM usage and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Read memory info
        try:
            with open("/proc/meminfo", "r") as f:
                meminfo = f.read()
                total_gb = int(meminfo.split("MemTotal:")[1].split()[0]) / 1024 / 1024
                available_gb = int(meminfo.split("MemAvailable:")[1].split()[0]) / 1024 / 1024
        except FileNotFoundError:
            import psutil
            memory = psutil.virtual_memory()
            total_gb = memory.total / (1024 * 1024)
            available_gb = memory.available / (1024 * 1024)

        used_gb = total_gb - available_gb
        percent_used = (used_gb / total_gb) * 100

        state["timestamp"] = datetime.now(timezone.utc).isoformat()
        state["total_gb"] = round(total_gb, 2)
        state["used_gb"] = round(used_gb, 2)
        state["available_gb"] = round(available_gb, 2)
        state["percent"] = round(percent_used, 2)

        self._save_state(plugin_dir, state)
        self._append_summary(plugin_dir, state)

        return {
            "timestamp": state["timestamp"],
            "total_gb": state["total_gb"],
            "used_gb": state["used_gb"],
            "available_gb": state["available_gb"],
            "percent": state["percent"],
        }
