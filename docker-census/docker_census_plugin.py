import json
import os
from datetime import datetime, timezone
import docker

from harness.shitpost_base import Shitpost


class DockerCensusPlugin(Shitpost):
    """Run a container census and emit results."""

    name = "docker-census"
    internal = True
    commit_template = "docker: {running}/{total} running"

    def __init__(self):
        super().__init__()
        self._log_file_name = "docker_log.jsonl"

    def _persisted_state_path(self) -> str:
        return os.path.join(self._plugin_dir(), "docker_summary.json")

    def _append_log(self, plugin_dir: str, log_entry: dict) -> None:
        path = os.path.join(plugin_dir, self._log_file_name)
        with open(path, "a", encoding="utf-8") as f:
            json.dump(log_entry, f)
            f.write("\n")

    def produce(self) -> dict:
        """Return the current Docker container census and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({"containers": {}})

        client = docker.from_env()

        containers = []
        running_count = 0
        containers_list = list(client.containers.list(all=True))
        total_count = len(containers_list)

        for container in containers_list:
            info = container.attrs
            restart_count = info['RestartCount']
            status = container.status
            is_running = status == 'running'
            running_count += 1 if is_running else 0

            containers.append({
                "name": container.name,
                "image": container.image.tags[0] if container.image.tags else "",
                "status": status,
                "running": is_running,
                "restart_count": restart_count
            })

        state["containers"] = {c['name']: c for c in containers}

        self._save_persisted_state(state)
        for container in containers:
            self._append_log(plugin_dir, container)

        return {
            "tick": len(state["containers"]),
            "running": running_count,
            "total": total_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
