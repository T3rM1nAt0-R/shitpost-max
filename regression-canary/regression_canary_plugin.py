"""Sends the same prompt to the same model every day and diffs the output, because silent regressions are how empires fall."""

import json
import os
import sys
import requests
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
        # Real bug, found 2026-07-17: these used to be "state.jsonl" and
        # "summary.json" -- the exact filenames the harness's own
        # _append_state()/_write_summary() write to automatically. This
        # plugin's own _save_state() truncates-and-rewrites that same file
        # (open(..., "w")) every tick with only its own tracked prompt
        # history, which then made _load_state()'s required-keys check fail
        # on the harness's differently-shaped appended line, silently
        # discarding all history on the very next tick. Renamed to distinct
        # filenames so the plugin's own state and the harness's automatic
        # log never collide.
        self._state_file_name = "regression_canary_prompt_history.jsonl"
        self._summary_file_name = "regression_canary_summary.json"
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
        prompts_evaluated = 0
        total_edit_ratio = 0.0

        for prompt in self.prompts:
            response = self.send_prompt(prompt["prompt"])
            if not response:
                continue

            prompts_evaluated += 1

            previous_output = next((item["output"] for item in state if item["prompt_id"] == prompt["id"]), None)
            edit_ratio, similarity = self.diff_outputs(previous_output, response)

            changed = edit_ratio < 0.98
            if changed:
                changed_count += 1

            total_edit_ratio += edit_ratio

            state.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "prompt_id": prompt["id"],
                "output": response,
                "edit_ratio": edit_ratio,
                "similarity": similarity,
                "changed": changed
            })

        if summary and prompts_evaluated > 0:
            avg_edit_ratio = (
                (summary.get("avg_edit_ratio", 0) * summary.get("prompts_evaluated", 0) + total_edit_ratio)
                / (summary.get("prompts_evaluated", 0) + prompts_evaluated)
            )
        elif prompts_evaluated > 0:
            avg_edit_ratio = total_edit_ratio / prompts_evaluated
        else:
            avg_edit_ratio = 0.0

        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "changed_count": changed_count,
            "avg_edit_ratio": avg_edit_ratio,
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
        # Real bugs, found 2026-07-17, all three causing this to fail on
        # every single call: (1) port 11434 is Ollama's own internal
        # default, but this host's actual Ollama container only exposes
        # port 1601 -- 11434 is unreachable, every request connection-
        # refused. (2) "qwen2.5:7b" isn't a pulled model tag on this host;
        # the actual tag is "qwen2.5-coder:7b-instruct-q6_K". (3) "stream"
        # wasn't set to false, so Ollama's default streaming response
        # (newline-delimited JSON chunks) would have broken response.json()
        # even once the first two bugs were fixed -- confirmed live.
        model = os.getenv("MODEL", "qwen2.5-coder:7b-instruct-q6_K")
        endpoint = os.getenv("LLM_ENDPOINT", "http://localhost:1601/api/generate")
        temperature = float(os.getenv("TEMPERATURE", 0.0))

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }

        try:
            response = requests.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            print(f"error: failed to send prompt '{prompt}' to model '{model}': {e}", file=sys.stderr)
            return ""

    def diff_outputs(self, previous_output: str, current_output: str) -> tuple:
        """Compute the edit ratio and similarity between two outputs.

        Real bug fixed 2026-07-17 (DeepSeek review): this imported
        `Levenshtein` and `sentence_transformers` (which pulls in torch) --
        neither is installed, neither is in requirements.txt, and this path
        is only reachable once a previous_output actually exists (i.e.
        never on a plugin's very first tick, which is all my own earlier
        fix-verification runs happened to exercise) -- so this would have
        ImportError'd and silently failed every tick from the second one
        onward. Replaced with stdlib difflib.SequenceMatcher, which gives a
        comparable 0-1 similarity ratio with no new dependency.
        """
        if not previous_output or not current_output:
            return 1.0, 0.0

        from difflib import SequenceMatcher

        similarity = SequenceMatcher(None, previous_output, current_output).ratio()
        edit_ratio = similarity  # same 0-1 scale this plugin's own "changed = edit_ratio < 0.98" check expects

        return edit_ratio, similarity
