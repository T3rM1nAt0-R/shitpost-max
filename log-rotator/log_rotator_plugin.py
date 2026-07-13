#!/usr/bin/env python3
"""Cron entry point for the log-rotator plugin."""

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
    commit_template = "rotate: {files_kept} files kept, old_size={old_size} gz_size={gz_size}"

    def __init__(self):
        super().__init__()
        self._log_file_name = "app.log"
        self._audit_log_file_name = "rotation_audit.jsonl"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it at rotation 0."""
        path = os.path.join(plugin_dir, "rotation_state.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: rotation state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"rotation", "tick"}
            if not required.issubset(state.keys()):
                print(
                    "warning: rotation state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            # The next number to emit is always ``a``; ``b`` is the one after.
            "rotation": 0,
            "tick": 0,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, "rotation_state.json")
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _rotate_log(self, plugin_dir: str) -> None:
        log_file = os.path.join(plugin_dir, self._log_file_name)
        audit_log_file = os.path.join(plugin_dir, self._audit_log_file_name)
        rotation = self._load_state(plugin_dir)["rotation"]

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

        self._save_state(plugin_dir, {"rotation": rotation + 1, "tick": 0})

    def produce(self) -> dict:
        """Return the next Fibonacci number and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        tick = state["tick"] + 1

        if tick % 60 == 0:
            self._rotate_log(plugin_dir)

        return {
            "tick": tick,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
