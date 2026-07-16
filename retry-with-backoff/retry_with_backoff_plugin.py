"""Built exponential backoff so my failures fail more gracefully than my successes succeed. Resilience-as-a-service."""

import json
import os
import subprocess
from datetime import datetime, timezone
import random
import time

from harness.shitpost_base import Shitpost


class RetryWithBackoffPlugin(Shitpost):
    """Retry client with exponential backoff."""

    name = "retry-with-backoff"
    internal = False
    commit_template = "retry: {result} after {attempts} attempts in {elapsed}s"

    def __init__(self):
        super().__init__()

    def produce(self) -> dict:
        """Return the retry result and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state(default={"attempt": 0, "elapsed": 0.0, "jitter_enabled": True})
        attempt = state["attempt"]
        elapsed = state["elapsed"]
        jitter_enabled = state["jitter_enabled"]

        base_delay_s = 1
        max_delay_s = 60
        max_retries = 10

        while True:
            result_proc = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                 "http://localhost:9999"],
                capture_output=True, text=True, timeout=10,
            )
            try:
                status_code = int(result_proc.stdout.strip())
            except (ValueError, TypeError):
                status_code = 999

            elapsed += base_delay_s

            if status_code < 500:
                break

            attempt += 1
            state["attempt"] = attempt
            state["elapsed"] = elapsed

            delay_used_s = min(base_delay_s * 2**attempt, max_delay_s)
            if jitter_enabled:
                delay_used_s *= random.uniform(0.5, 1.5)

            self._log_attempt(plugin_dir, attempt, delay_used_s, status_code)
            print(f"Attempt {attempt}: Delayed for {delay_used_s:.2f}s, got status code {status_code}")

            if attempt >= max_retries:
                break

            time.sleep(delay_used_s)

        if status_code < 500:
            result = "success"
        else:
            result = "failure"

        state["attempt"] = attempt
        state["elapsed"] = elapsed

        self._save_persisted_state(state)
        return {
            "result": result,
            "attempts": attempt,
            "elapsed": elapsed,
        }

    def _log_attempt(self, plugin_dir: str, attempt: int, delay_used_s: float, status_code: int) -> None:
        path = os.path.join(plugin_dir, "retry_log.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "attempt": attempt,
                "delay_used_s": delay_used_s,
                "status_code": status_code,
                "url": "http://localhost:9999",
            }) + "\n")
