#!/usr/bin/env python3
"""Cron entry point for the log-rotator plugin."""

import json
import os
import sys
import gzip
from datetime import datetime, timezone
import shutil

# Make the repo root importable so ``harness.shitpost_base`` is available.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from harness.shitpost_base import Shitpost  # noqa: E402


class LogRotatorPlugin(Shitpost):
    """Generate log lines and rotate the log file hourly."""

    name = "log-rotator"
    internal = False
    commit_template = "tick {tick} @ {timestamp}"

    def __init__(self):
        super().__init__()
        self._log_file_name = "app.log"
        self._audit_log_file_name = "rotation_audit.jsonl"

    def _persisted_state_path(self) -> str:
        """Preserve the original custom state filename so existing state isn't lost."""
        return os.path.join(self._plugin_dir(), "rotation_state.json")

    def _rotate_log(self, plugin_dir: str) -> None:
        log_file = os.path.join(plugin_dir, self._log_file_name)
        audit_log_file = os.path.join(plugin_dir, self._audit_log_file_name)
        rotation = self._load_persisted_state({"rotation": 0, "tick": 0})["rotation"]

        if os.path.exists(log_file):
            old_size = os.path.getsize(log_file)
            new_log_file = f"{log_file}.{rotation}"
            shutil.move(log_file, new_log_file)

            with gzip.open(f"{new_log_file}.gz", "wb") as f_out:
                with open(new_log_file, "rb") as f_in:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(new_log_file)

            gz_size = os.path.getsize(f"{new_log_file}.gz")
            files_kept = 5
            with open(audit_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "old_size_bytes": old_size,
                    "gz_size_bytes": gz_size,
                    "files_kept": files_kept
                }) + "\n")

            # Delete oldest if count > 5
            rotation_files = sorted([f for f in os.listdir(plugin_dir) if f.startswith(f"{log_file}.")])
            if len(rotation_files) > 5:
                oldest_file = rotation_files[0]
                os.remove(oldest_file)
                os.remove(f"{oldest_file}.gz")

        self._save_persisted_state({"rotation": rotation + 1, "tick": 0})

    def produce(self) -> dict:
        """Return the next Fibonacci number and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({"rotation": 0, "tick": 0})
        tick = state["tick"] + 1

        if tick % 60 == 0:
            self._rotate_log(plugin_dir)

        return {
            "tick": tick,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
