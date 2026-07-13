import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class ModelDiffPlugin(Shitpost):
    """Run a fixed evaluation suite against a new model version and commit the scorecard."""

    name = "model-diff"
    internal = False
    commit_template = "model-diff: {model_name} — factual {factual_acc:.0%}, instruct {instruction_pass:.0%} ({regression_count} regressions)"

    def __init__(self):
        super().__init__()
        self._state_file_name = "model_diff_state.json"
        self._scorecards_dir = "scorecards"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running model state, or initialise it at initial state."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: model-diff state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"model_name", "model_hash", "last_updated"}
            if not required.issubset(state.keys()):
                print(
                    "warning: model-diff state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "model_name": None,
            "model_hash": None,
            "last_updated": None,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _detect_model(self) -> dict:
        import subprocess
        result = subprocess.run([os.getenv("MODEL_DETECT_CMD", "ollama list")], capture_output=True, text=True)
        models = json.loads(result.stdout)
        for model in models:
            if model["name"] == os.getenv("MODEL_NAME"):
                return {
                    "model_name": model["name"],
                    "model_hash": model.get("digest"),
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                }
        return None

    def _run_eval_suite(self) -> dict:
        from evals.factual import run_factual
        from evals.instruction import run_instruction
        from evals.safety import run_safety
        from evals.json_schemas import run_json_schemas
        from evals.latency import run_latency

        factual_acc = run_factual()
        instruction_pass = run_instruction()
        safety_pass = run_safety()
        json_compliance = run_json_schemas()
        latency_tps = run_latency()

        return {
            "factual_acc": factual_acc,
            "instruction_pass": instruction_pass,
            "safety_pass": safety_pass,
            "json_compliance": json_compliance,
            "latency_tps": latency_tps,
        }

    def _generate_scorecard(self, current_results: dict) -> str:
        scorecards = sorted([f for f in os.listdir(self._scorecards_dir) if f.endswith(".md")], reverse=True)
        if scorecards:
            with open(os.path.join(self._scorecards_dir, scorecards[0]), "r", encoding="utf-8") as f:
                previous_results = json.loads(f.read())
        else:
            previous_results = {}

        diff_table = []
        for key in ["factual_acc", "instruction_pass", "safety_pass", "json_compliance"]:
            current_value = current_results.get(key, 0)
            previous_value = previous_results.get(key, 0)
            if current_value > previous_value:
                diff_table.append(f"{key}: {current_value:.2%} (↑)")
            elif current_value < previous_value:
                diff_table.append(f"{key}: {current_value:.2%} (↓)")
            else:
                diff_table.append(f"{key}: {current_value:.2%}")

        return "\n".join(diff_table)

    def produce(self) -> dict:
        """Return the evaluation results and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)
        os.makedirs(self._scorecards_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        current_model_info = self._detect_model()

        if not current_model_info or current_model_info["model_hash"] == state.get("model_hash"):
            return None

        results = self._run_eval_suite()
        scorecard_content = self._generate_scorecard(results)

        scorecard_path = os.path.join(self._scorecards_dir, f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}_{current_model_info['model_name']}.md")
        with open(scorecard_path, "w", encoding="utf-8") as f:
            f.write(scorecard_content)

        state["model_name"] = current_model_info["model_name"]
        state["model_hash"] = current_model_info["model_hash"]
        state["last_updated"] = datetime.now(timezone.utc).isoformat()

        self._save_state(plugin_dir, state)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model_name": current_model_info["model_name"],
            "model_hash": current_model_info["model_hash"],
            "action": "eval_run",
            **results,
            "regression_count": sum(1 for line in scorecard_content.splitlines() if "(↓)" in line),
            "improvement_count": sum(1 for line in scorecard_content.splitlines() if "(↑)" in line),
        }
