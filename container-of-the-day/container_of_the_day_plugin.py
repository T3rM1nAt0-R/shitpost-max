import json
import os
import sys
from datetime import datetime, timezone
import subprocess

from harness.shitpost_base import Shitpost


class ContainerOfTheDayPlugin(Shitpost):
    """Build and run a Docker image daily."""

    name = "container-of-the-day"
    internal = False
    commit_template = "cotd: day {day} built in {build_duration_s:.2f}s, size={image_size_bytes}B"

    def __init__(self):
        super().__init__()

    def _persisted_state_path(self) -> str:
        """Return the original state file path so existing state is preserved."""
        return os.path.join(self._plugin_dir(), "cotd_state.json")

    def _append_log(self, plugin_dir: str, log_entry: dict) -> None:
        path = os.path.join(plugin_dir, "container_log.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

    def produce(self) -> dict | None:
        """Return the next Docker build and run result."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({"day": 0, "tick": 0})

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
            # docker build -q returns a full sha256:<digest> image ID, not an
            # overlay2 directory name (those use internal opaque layer IDs) --
            # `docker inspect` is the correct, portable way to get an image's
            # real size, not guessing a filesystem path under
            # /var/lib/docker/overlay2.
            image_size_bytes = int(
                subprocess.run(
                    ["docker", "inspect", "-f", "{{.Size}}", image_id],
                    capture_output=True, text=True, check=True,
                ).stdout.strip()
            )

            log_entry = {
                "date": datetime.now(timezone.utc).isoformat(),
                "image_id": image_id,
                "build_duration_s": build_duration_s,
                "image_size_bytes": image_size_bytes,
                "container_output": container_output
            }

            self._save_persisted_state(state)
            self._append_log(plugin_dir, log_entry)

            return {
                "tick": tick,
                "day": day,
                "build_duration_s": build_duration_s,
                "image_size_bytes": image_size_bytes,
                "container_output": container_output,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except (subprocess.CalledProcessError, OSError) as e:
            print(f"error: {e}", file=sys.stderr)
            return None
