import json
import os
import random
from datetime import datetime, timezone
import subprocess

from harness.shitpost_base import Shitpost


class ContainerOfTheDayPlugin(Shitpost):
    """Build and run a Docker image daily."""

    name = "container-of-the-day"
    internal = False
    commit_template = "cotd: build {id} size={size} duration={dur}s"

    def __init__(self):
        super().__init__()
        self._state_file_name = "cotd_state.json"
        self._log_file_name = "container_log.jsonl"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it at day 0."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: cotd state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"day", "tick"}
            if not required.issubset(state.keys()):
                print(
                    "warning: cotd state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            # The next day to emit is always ``day``; ``tick`` is the one after.
            "day": 0,
            "tick": 0,
        }

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
            f.write(json.dumps(log_entry) + "\n")

    def produce(self) -> dict | None:
        """Return the next Docker build and run result."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Emit the next day, then advance the counter.
        day = state["day"]
        state["day"] += 1

        tick = state["tick"]
        state["tick"] += 1

        try:
            start_time = datetime.now(timezone.utc)
            build_output = subprocess.run(["docker", "build", "-q", "."], capture_output=True, text=True, check=True)
            image_id = build_output.stdout.strip()
            end_time = datetime.now(timezone.utc)

            run_output = subprocess.run(["docker", "run", "--rm", image_id], capture_output=True, text=True, check=True)
            container_output = run_output.stdout.strip()

            build_duration_s = (end_time - start_time).total_seconds()
            image_size_bytes = int(subprocess.run(["du", "-b", f"/var/lib/docker/overlay2/{image_id}/merged"], capture_output=True, text=True, check=True).stdout.split()[0])

            log_entry = {
                "date": datetime.now(timezone.utc).isoformat(),
                "image_id": image_id,
                "build_duration_s": build_duration_s,
                "image_size_bytes": image_size_bytes,
                "container_output": container_output
            }

            self._save_state(plugin_dir, state)
            self._append_log(plugin_dir, log_entry)

            return {
                "tick": tick,
                "day": day,
                "build_duration_s": build_duration_s,
                "image_size_bytes": image_size_bytes,
                "container_output": container_output,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except subprocess.CalledProcessError as e:
            print(f"error: {e}", file=sys.stderr)
            return None
