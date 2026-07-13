import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List

from harness.shitpost_base import Shitpost


class RegressionCanaryPlugin(Shitpost):
    """Daily tick that sends the same fixed prompt to a local LLM and diffs the output against the previous tick."""

    name = "regression-canary"
    internal = False
    commit_template = "regression-canary: {changed_count}/{prompts_evaluated} prompts changed"

    def __init__(self):
        super().__init__()
        self._state_file_name = "state.jsonl"
        self._summary_file_name = "summary.json"
        self.prompts = [
            {"id": "joke", "prompt": "Tell me a joke."},
            {"id": "weather", "prompt": "What's the weather like today?"},
            {"id": "news", "prompt": "Summarize the latest news."},
            {"id": "recipe", "prompt": "Give me a recipe for pizza."},
            {"id": "history", "prompt": "Tell me about the history of computers."},
            {"id": "science", "prompt": "Explain the theory of relativity."},
            {"id": "math", "prompt": "Solve this equation: 2 + 2 = ?"},
            {"id": "art", "prompt": "Describe your favorite painting."},
            {"id": "music", "prompt": "What's a good song to listen to?"},
            {"id": "sports", "prompt": "Tell me about the latest sports scores."}
        ]

    def _load_state(self, plugin_dir: str) -> List[Dict]:
        """Load the running state, or initialise it at empty."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = [json.loads(line) for line in f]
            except json.JSONDecodeError as exc:
                print(
                    f"warning: regression-canary state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return []
            # Guard against manual tampering / old versions.
            required_keys = {"timestamp", "prompt_id", "output", "edit_ratio", "similarity", "changed"}
            if not all(required_keys.issubset(item.keys()) for item in state):
                print(
                    "warning: regression-canary state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return []
            return state

        return []

    def _save_state(self, plugin_dir: str, state: List[Dict]) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            for item in state:
                json.dump(item, f)
                f.write("\n")
        os.replace(tmp_path, path)

    def _load_summary(self, plugin_dir: str) -> Dict:
        """Load the previous summary, or initialise it at empty."""
        path = os.path.join(plugin_dir, self._summary_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    summary = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: regression-canary summary file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return {}
            # Guard against manual tampering / old versions.
            required_keys = {"timestamp", "changed_count", "avg_edit_ratio", "prompts_evaluated"}
            if not required_keys.issubset(summary.keys()):
                print(
                    "warning: regression-canary summary missing keys; starting fresh",
                    file=sys.stderr,
                )
                return {}
            return summary

        return {}

    def _save_summary(self, plugin_dir: str, summary: Dict) -> None:
        path = os.path.join(plugin_dir, self._summary_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(summary, f)
        os.replace(tmp_path, path)

    def produce(self) -> Dict:
        """Return the diff metrics for each prompt and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        summary = self._load_summary(plugin_dir)

        changed_count = 0
        prompts_evaluated = len(self.prompts)

        for prompt in self.prompts:
            response = self.send_prompt(prompt["prompt"])
            if not response:
                continue

            previous_output = next((item["output"] for item in state if item["prompt_id"] == prompt["id"]), None)
            edit_ratio, similarity = self.diff_outputs(previous_output, response)

            changed = edit_ratio < 0.98
            if changed:
                changed_count += 1

            state.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "prompt_id": prompt["id"],
                "output": response,
                "edit_ratio": edit_ratio,
                "similarity": similarity,
                "changed": changed
            })

        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "changed_count": changed_count,
            "avg_edit_ratio": (summary.get("avg_edit_ratio", 0) * summary.get("prompts_evaluated", 0) + edit_ratio) / prompts_evaluated if summary else edit_ratio,
            "prompts_evaluated": prompts_evaluated
        }

        self._save_state(plugin_dir, state)
        self._save_summary(plugin_dir, summary)

        return {
            "changed_count": changed_count,
            "prompts_evaluated": prompts_evaluated,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def send_prompt(self, prompt: str) -> str:
        """Send a prompt to the LLM and return the response."""
        model = os.getenv("MODEL", "qwen2.5:7b")
        endpoint = os.getenv("LLM_ENDPOINT", "http://localhost:11434/api/generate")
        temperature = float(os.getenv("TEMPERATURE", 0.0))

        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature
        }

        try:
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json().get("output", "")
        except Exception as e:
            print(f"error: failed to send prompt '{prompt}' to model '{model}': {e}", file=sys.stderr)
            return ""

    def diff_outputs(self, previous_output: str, current_output: str) -> tuple:
        """Compute the edit ratio and similarity between two outputs."""
        if not previous_output or not current_output:
            return 1.0, 0.0

        from Levenshtein import distance
        from sentence_transformers import SentenceTransformer, util

        levenshtein_ratio = distance(previous_output, current_output) / max(len(previous_output), len(current_output))
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode([previous_output, current_output])
        similarity = util.cos_sim(embeddings[0], embeddings[1])[0][0]

        return levenshtein_ratio, similarity
