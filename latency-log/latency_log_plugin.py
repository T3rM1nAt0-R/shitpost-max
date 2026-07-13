import json
import os
import sys
from datetime import datetime, timezone
import subprocess

from harness.shitpost_base import Shitpost


class LatencyLogPlugin(Shitpost):
    """ICMP latency logger from the i7 host."""

    name = "latency-log"
    internal = True
    commit_template = "latency: cloudflare {cf_avg_ms}ms, domain {domain_avg_ms}ms"

    def __init__(self):
        super().__init__()
        self._state_file_name = "latency_state.json"
        self._log_file_name = "latency_log.jsonl"
        self._summary_file_name = "latency_summary.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running latency state."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: latency state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"tick", "cloudflare", "domain"}
            if not required.issubset(state.keys()):
                print(
                    "warning: latency state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "tick": 0,
            "cloudflare": {"avg_ms": None, "packet_loss": None},
            "domain": {"avg_ms": None, "packet_loss": None}
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

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
                packet_loss = int(line.split("%")[0])

        return {"avg_ms": avg_ms, "packet_loss": packet_loss}

    def produce(self) -> dict:
        """Return the ICMP latency and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        tick = state["tick"] + 1

        targets = ["1.1.1.1", "nirajsangani.com"]
        ping_count = 3

        for target in targets:
            result = self._ping(target, ping_count)
            avg_ms = result["avg_ms"]
            packet_loss = result["packet_loss"]

            state[target]["avg_ms"] = avg_ms
            state[target]["packet_loss"] = packet_loss

            self._append_log(plugin_dir, target, avg_ms, packet_loss)

        state["tick"] = tick
        self._save_state(plugin_dir, state)
        self._update_summary(plugin_dir, state)

        return {
            "tick": tick,
            "cloudflare_avg_ms": state["cloudflare"]["avg_ms"],
            "domain_avg_ms": state["domain"]["avg_ms"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
