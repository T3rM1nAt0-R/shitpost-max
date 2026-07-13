import glob
import json
import os
import subprocess
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class TempLogPlugin(Shitpost):
    """CPU temperature logger for the i7 host."""

    name = "temp-log"
    internal = True
    commit_template = "temp: package {pkg_temp_c}°C"

    def __init__(self):
        super().__init__()
        self._log_file_name = "temp_log.jsonl"
        self._summary_file_name = "temp_summary.json"

    def _append_log(self, plugin_dir: str, log_entry: dict) -> None:
        path = os.path.join(plugin_dir, self._log_file_name)
        with open(path, "a", encoding="utf-8") as f:
            json.dump(log_entry, f)
            f.write("\n")

    def _update_summary(self, plugin_dir: str, summary: dict) -> None:
        path = os.path.join(plugin_dir, self._summary_file_name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary, f)

    def produce(self) -> dict:
        """Return the CPU temperature and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({"tick": 0, "sensors": {}})

        # Discover sensors
        sensors = self._discover_sensors()
        if not sensors:
            return None

        # Update sensor data
        for label, temp_c in sensors.items():
            state["sensors"][label] = temp_c

        # Find package temperature
        pkg_temp_c = next((temp_c for label, temp_c in sensors.items() if "Package" in label or "Tctl" in label), None)
        if not pkg_temp_c:
            return None

        # Append log entry
        log_entry = {
            "tick": state["tick"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **sensors,
        }
        self._append_log(plugin_dir, log_entry)

        # Update summary
        summary = {label: temp_c for label, temp_c in sensors.items()}
        self._update_summary(plugin_dir, summary)

        state["tick"] += 1

        return {
            "tick": state["tick"],
            "pkg_temp_c": pkg_temp_c,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _discover_sensors(self) -> dict:
        """Discover CPU thermal sensors."""
        hwmon_dir = None
        try:
            with open("/sys/class/hwmon/hwmon*/name", "r") as f:
                for line in f:
                    if "coretemp" in line:
                        hwmon_dir = os.path.dirname(f.name)
                        break
        except FileNotFoundError:
            pass

        sensors = {}
        if hwmon_dir:
            for temp_file in glob.glob(os.path.join(hwmon_dir, "temp*_input")):
                with open(temp_file, "r") as f:
                    temp_c = int(f.read().strip()) / 1000
                label = os.path.basename(temp_file).replace("temp", "").replace("_input", "")
                sensors[label] = temp_c
        else:
            try:
                output = subprocess.check_output([self._get_sensors_cmd(), "-u"], text=True)
                for line in output.splitlines():
                    if "Package" in line or "Tctl" in line:
                        parts = line.split()
                        label = parts[0]
                        temp_c = float(parts[-1])
                        sensors[label] = temp_c
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass

        return sensors

    def _get_sensors_cmd(self) -> str:
        """Get the command to run for sensor discovery."""
        return os.getenv("SENSORS_CMD", "sensors -u")
