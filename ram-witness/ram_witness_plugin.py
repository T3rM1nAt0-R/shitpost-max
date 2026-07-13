import json
import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class RamWitnessPlugin(Shitpost):
    """Memory-pressure logger for the i7 host."""

    name = "ram-witness"
    internal = True
    commit_template = "ram: {percent}% used ({used_gb}GB / {total_gb}GB)"

    def __init__(self):
        super().__init__()
        self._summary_file_name = "ram_summary.json"

    def _append_summary(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._summary_file_name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)

    def produce(self) -> dict:
        """Return the current RAM usage and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "timestamp": None,
            "total_gb": 0,
            "used_gb": 0,
            "available_gb": 0,
            "percent": 0.0,
        })

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

        self._save_persisted_state(state)
        self._append_summary(plugin_dir, state)

        return {
            "timestamp": state["timestamp"],
            "total_gb": state["total_gb"],
            "used_gb": state["used_gb"],
            "available_gb": state["available_gb"],
            "percent": state["percent"],
        }
