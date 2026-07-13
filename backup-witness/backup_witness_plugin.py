#!/usr/bin/env python3
"""Cron entry point for the backup-witness plugin."""

import json
import os
import sys
from datetime import datetime, timezone

# Make the repo root importable so ``harness.shitpost_base`` is available.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from harness.shitpost_base import Shitpost  # noqa: E402


class BackupWitnessPlugin(Shitpost):
    """Backup freshness witness for the i7 host."""

    name = "backup-witness"
    internal = True
    commit_template = "backup: backup.sh {backup_sh_hours_since}h ago, kopia {kopia_hours_since}h ago"

    def __init__(self):
        super().__init__()
        self._state_file_name = "backup_log.jsonl"
        self._summary_file_name = "backup_summary.json"
        self._backup_repo = os.getenv("BACKUP_REPO", "/home/niraj/i7-backup")
        self._warning_hours = int(os.getenv("WARNING_HOURS", 26))

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running backup state."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: backup witness state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "backup_sh_hours_since": None,
            "kopia_hours_since": None,
            "ok": False,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _update_summary(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._summary_file_name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state["ok"], f)

    def produce(self) -> dict | None:
        """Return the backup witness status and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        try:
            # Get the latest backup.sh commit time
            backup_sh_timestamp = subprocess.check_output(
                ["git", "-C", self._backup_repo, "log", "-1", "--format=%cI"],
                text=True,
            ).strip()
            backup_sh_datetime = datetime.fromisoformat(backup_sh_timestamp)
        except subprocess.CalledProcessError as e:
            print(f"error: failed to get backup.sh commit time ({e})", file=sys.stderr)
            return None

        try:
            # Get the latest Kopia snapshot timestamp
            kopia_output = subprocess.check_output(
                ["kopia", "snapshot", "list", "--json"],
                text=True,
            )
            snapshots = json.loads(kopia_output)
            if not snapshots:
                raise ValueError("No Kopia snapshots found")
            latest_snapshot = max(snapshots, key=lambda s: s["endTime"])
            kopia_datetime = datetime.fromisoformat(latest_snapshot["endTime"])
        except subprocess.CalledProcessError as e:
            print(f"error: failed to get Kopia snapshot list ({e})", file=sys.stderr)
            return None
        except json.JSONDecodeError as e:
            print(f"error: invalid JSON from kopia snapshot list ({e})", file=sys.stderr)
            return None

        # Compute hours since each source ran
        now = datetime.now(timezone.utc)
        backup_sh_hours_since = (now - backup_sh_datetime).total_seconds() / 3600
        kopia_hours_since = (now - kopia_datetime).total_seconds() / 3600

        state["backup_sh_hours_since"] = backup_sh_hours_since
        state["kopia_hours_since"] = kopia_hours_since
        state["ok"] = backup_sh_hours_since <= self._warning_hours and kopia_hours_since <= self._warning_hours

        self._save_state(plugin_dir, state)
        self._update_summary(plugin_dir, state)

        return {
            "backup_sh_timestamp": backup_sh_timestamp,
            "kopia_timestamp": latest_snapshot["endTime"],
            "backup_sh_hours_since": backup_sh_hours_since,
            "kopia_hours_since": kopia_hours_since,
            "ok": state["ok"],
            "timestamp": now.isoformat(),
        }
