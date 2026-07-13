import json
import os
import sys
from datetime import datetime, timezone
import random

from harness.shitpost_base import Shitpost


class RetryWithBackoffPlugin(Shitpost):
    """Retry client with exponential backoff."""

    name = "retry-with-backoff"
    internal = False
    commit_template = "retry: {result} after {attempts} attempts in {elapsed}s"

    def __init__(self):
        super().__init__()
        self._state_file_name = "retry_state.json"
        self._log_file_name = "retry_log.jsonl"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running retry state, or initialise it at attempt 0."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: retry state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"attempt", "elapsed", "jitter_enabled"}
            if not required.issubset(state.keys()):
                print(
                    "warning: retry state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "attempt": 0,
            "elapsed": 0.0,
            "jitter_enabled": True,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _log_attempt(self, plugin_dir: str, attempt: int, delay_used_s: float, status_code: int) -> None:
        path = os.path.join(plugin_dir, self._log_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "attempt": attempt,
                "delay_used_s": delay_used_s,
                "status_code": status_code,
                "url": "http://localhost:9999",
            }) + "\n")

    def produce(self) -> dict:
        """Return the retry result and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        attempt = state["attempt"]
        elapsed = state["elapsed"]
        jitter_enabled = state["jitter_enabled"]

        base_delay_s = 1
        max_delay_s = 60
        max_retries = 10

        while True:
            response = os.system("curl -s -o /dev/null -w \"%{http_code}\" http://localhost:9999")
            elapsed += base_delay_s

            if response < 500:
                break

            attempt += 1
            state["attempt"] = attempt
            state["elapsed"] = elapsed

            delay_used_s = min(base_delay_s * 2**attempt, max_delay_s)
            if jitter_enabled:
                delay_used_s *= random.uniform(0.5, 1.5)

            self._log_attempt(plugin_dir, attempt, delay_used_s, response)
            print(f"Attempt {attempt}: Delayed for {delay_used_s:.2f}s, got status code {response}")
            time.sleep(delay_used_s)

        if response < 500:
            result = "success"
        else:
            result = "failure"

        state["attempt"] = attempt
        state["elapsed"] = elapsed

        self._save_state(plugin_dir, state)
        return {
            "result": result,
            "attempts": attempt,
            "elapsed": elapsed,
        }
