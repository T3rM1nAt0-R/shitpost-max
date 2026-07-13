import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class LitellmTokensPlugin(Shitpost):
    """Daily token-spend logger for the AI models used in this project."""

    name = "litellm-tokens"
    internal = True
    commit_template = "tokens: {total_usd} today across {model_count} models"

    def __init__(self):
        super().__init__()
        self._state_file_name = "last_counters.json"
        self._log_file_name = "tokens_log.jsonl"
        self._summary_file_name = "tokens_summary.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it at first run."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: litellm tokens state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return {}
            return state

        return {}

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
            json.dump(log_entry, f)
            f.write("\n")

    def _update_summary(self, plugin_dir: str, summary: dict) -> None:
        path = os.path.join(plugin_dir, self._summary_file_name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary, f)

    def produce(self) -> dict | None:
        """Return the token spend and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        current_counters = {}

        try:
            response = requests.get(os.getenv("LITELLM_METRICS_URL"))
            response.raise_for_status()
            metrics_text = response.text
        except Exception as e:
            print(f"error: failed to fetch metrics ({e})", file=sys.stderr)
            return None

        for line in metrics_text.splitlines():
            if "litellm_spend_total" in line or "litellm_total_tokens" in line:
                parts = line.split()
                model = parts[0].split('{')[1].split('}')[0]
                spend_total = float(parts[2])
                tokens_total = int(parts[4])

                current_counters[model] = {
                    "spend_total": spend_total,
                    "tokens_total": tokens_total
                }

        if not current_counters:
            print("warning: no metrics found", file=sys.stderr)
            return None

        log_entries = []
        summary = {}

        for model, counters in current_counters.items():
            last_counters = state.get(model, {})
            spend_delta = counters["spend_total"] - last_counters.get("spend_total", 0)
            tokens_delta = counters["tokens_total"] - last_counters.get("tokens_total", 0)

            log_entry = {
                "model": model,
                "input_tokens": tokens_delta,
                "output_tokens": tokens_delta,  # Assuming equal input and output for simplicity
                "cost_usd": spend_delta
            }
            log_entries.append(log_entry)

            summary[model] = {
                "total_spend": counters["spend_total"],
                "total_tokens": counters["tokens_total"]
            }

        state.update(current_counters)
        self._save_state(plugin_dir, state)
        for entry in log_entries:
            self._append_log(plugin_dir, entry)
        self._update_summary(plugin_dir, summary)

        total_usd = sum(entry["cost_usd"] for entry in log_entries)
        model_count = len(log_entries)

        return {
            "total_usd": total_usd,
            "model_count": model_count,
            "log_entries": log_entries,
            "summary": summary,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
