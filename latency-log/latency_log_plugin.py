import json
import os
import re
from datetime import datetime, timezone
import subprocess

from harness.shitpost_base import Shitpost


class LatencyLogPlugin(Shitpost):
    """ICMP latency logger from the i7 host."""

    name = "latency-log"
    internal = True
    commit_template = "latency: cloudflare {cloudflare_avg_ms}ms, domain {domain_avg_ms}ms"

    def __init__(self):
        super().__init__()
        self._log_file_name = "latency_log.jsonl"
        self._summary_file_name = "latency_summary.json"

    def _persisted_state_path(self) -> str:
        return os.path.join(self._plugin_dir(), "latency_state.json")

    def _append_log(self, plugin_dir: str, target: str, avg_ms: float, packet_loss: int) -> None:
        path = os.path.join(plugin_dir, self._log_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"target": target, "avg_ms": avg_ms, "packet_loss": packet_loss}) + "\n")

    def _update_summary(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._summary_file_name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)

    def _ping(self, target: str, count: int) -> dict:
        result = subprocess.run(["ping", "-c", str(count), "-W", "1", target], capture_output=True, text=True)
        lines = result.stdout.splitlines()
        avg_ms = None
        packet_loss = 0

        for line in lines:
            if "time=" in line:
                avg_ms = float(line.split("time=")[1].split()[0])
            elif "packet loss" in line:
                m = re.search(r"(\d+)% packet loss", line)
                packet_loss = int(m.group(1)) if m else packet_loss

        return {"avg_ms": avg_ms, "packet_loss": packet_loss}

    def produce(self) -> dict:
        """Return the ICMP latency and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "tick": 0,
            "cloudflare": {"avg_ms": None, "packet_loss": None},
            "domain": {"avg_ms": None, "packet_loss": None}
        })
        tick = state["tick"] + 1

        targets = [("1.1.1.1", "cloudflare"), ("nirajsangani.com", "domain")]
        ping_count = 3

        for target, state_key in targets:
            result = self._ping(target, ping_count)
            avg_ms = result["avg_ms"]
            packet_loss = result["packet_loss"]

            target_state = state.setdefault(state_key, {})
            target_state["avg_ms"] = avg_ms
            target_state["packet_loss"] = packet_loss

            self._append_log(plugin_dir, target, avg_ms, packet_loss)

        state["tick"] = tick
        self._save_persisted_state(state)
        self._update_summary(plugin_dir, state)

        return {
            "tick": tick,
            "cloudflare_avg_ms": state["cloudflare"]["avg_ms"],
            "domain_avg_ms": state["domain"]["avg_ms"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
