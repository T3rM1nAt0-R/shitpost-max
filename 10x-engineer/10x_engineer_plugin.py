import json
import os
import sys
from datetime import datetime, timezone
from subprocess import run, PIPE

from harness.shitpost_base import Shitpost


class TenXEngineerPlugin(Shitpost):
    """Orchestrator that runs ten other shitpost-max scripts in a single tick."""

    name = "10x-engineer"
    internal = False
    commit_template = "10x: {ok}/{total} OK"

    def __init__(self):
        super().__init__()
        self._targets_file_name = "targets.txt"
        self._log_file_name = "orchestration-log.jsonl"

    def _load_targets(self, plugin_dir: str) -> list:
        """Load the list of target plugins from targets.txt."""
        path = os.path.join(plugin_dir, self._targets_file_name)
        if not os.path.exists(path):
            print(f"error: {path} does not exist", file=sys.stderr)
            return []

        with open(path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines()]

        targets = []
        for line in lines:
            parts = line.split(":")
            if len(parts) != 2:
                print(f"warning: invalid target entry '{line}'", file=sys.stderr)
                continue
            directory, entry_point = parts
            targets.append((directory.strip(), entry_point.strip()))

        return targets

    def _run_target(self, plugin_dir: str, target_dir: str, entry_point: str) -> dict:
        """Run a single target and capture the result."""
        try:
            result = run(
                [sys.executable, os.path.join(target_dir, entry_point)],
                cwd=target_dir,
                stdout=PIPE,
                stderr=PIPE,
                text=True,
            )
            return {
                "target": target_dir,
                "return_code": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            print(f"error: failed to run {target_dir}/{entry_point}: {e}", file=sys.stderr)
            return {
                "target": target_dir,
                "return_code": -1,
                "stdout": "",
                "stderr": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def _save_log(self, plugin_dir: str, log_entry: dict) -> None:
        """Append a log entry to orchestration-log.jsonl."""
        path = os.path.join(plugin_dir, self._log_file_name)
        with open(path, "a", encoding="utf-8") as f:
            json.dump(log_entry, f)
            f.write("\n")

    def produce(self) -> dict:
        """Run ten other shitpost-max scripts and log the results."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        targets = self._load_targets(plugin_dir)
        if not targets:
            return None

        ok_count = 0
        total_count = len(targets)

        for target_dir, entry_point in targets:
            log_entry = self._run_target(plugin_dir, target_dir, entry_point)
            self._save_log(plugin_dir, log_entry)
            if log_entry["return_code"] == 0:
                ok_count += 1

        return {
            "ok": ok_count,
            "total": total_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
