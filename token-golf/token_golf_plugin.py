import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional

from harness.shitpost_base import Shitpost


class TokenGolfPlugin(Shitpost):
    """Token golf plugin: shrink prompts while maintaining quality."""

    name = "token-golf"
    internal = False
    commit_template = "token-golf: {active_tokens}t ({pct_reduction:.0f}% from baseline), Q={quality}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "state.jsonl"
        self._task_file_name = "task.json"
        self._active_prompt_file_name = "active_prompt.json"

    @staticmethod
    def _default_state() -> Dict[str, List[Dict[str, str]]]:
        return {
            "candidates": [],
            "winner": None,
            "active_tokens": 0,
            "baseline_tokens": 0,
            "plateau_ticks": 0
        }

    def _load_state(self, plugin_dir: str) -> Dict[str, List[Dict[str, str]]]:
        """Load the running state, or initialise it at default."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: token-golf state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    def _save_state(self, plugin_dir: str, state: Dict[str, List[Dict[str, str]]]) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _load_task(self, plugin_dir: str) -> Dict[str, str]:
        """Load the task definition."""
        path = os.path.join(plugin_dir, self._task_file_name)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_active_prompt(self, plugin_dir: str, prompt: Dict[str, str]) -> None:
        """Save the current active prompt."""
        path = os.path.join(plugin_dir, self._active_prompt_file_name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(prompt, f)

    def _load_active_prompt(self, plugin_dir: str) -> Optional[Dict[str, str]]:
        """Load the current active prompt."""
        path = os.path.join(plugin_dir, self._active_prompt_file_name)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)

        return None

    def _generate_candidates(self, task: Dict[str, str], active_prompt: Dict[str, str]) -> List[Dict[str, str]]:
        """Generate 3-5 shorter candidates using rewrite rules."""
        candidates = []
        for rule in ["strip_modifiers", "remove_example", "condense_instruction", "remove_preamble"]:
            candidate = self._apply_rule(task["baseline_prompt"], rule)
            if candidate != task["baseline_prompt"]:
                candidates.append({"prompt": candidate, "tokens": len(candidate.split()), "score": 0})
        return candidates

    def _apply_rule(self, prompt: str, rule: str) -> str:
        """Apply a rewrite rule to the prompt."""
        if rule == "strip_modifiers":
            for modifier in ["please", "kindly", "carefully", "in detail", "thoroughly"]:
                prompt = prompt.replace(f" {modifier} ", " ")
        elif rule == "remove_example":
            prompt = " ".join([line for line in prompt.split("\n") if not line.strip().startswith(("For example", "e.g.", "For instance"))])
        elif rule == "condense_instruction":
            synonyms = {
                "Please provide a summary of": "Summarize",
                "Please generate a list of": "List"
            }
            for verbose, short in synonyms.items():
                prompt = prompt.replace(verbose, short)
        elif rule == "remove_preamble":
            sentences = prompt.split(". ")
            for i, sentence in enumerate(sentences):
                if any(sentence.strip().startswith(verb) for verb in ["summarize", "write", "list", "explain", "generate", "translate"]):
                    return ". ".join(sentences[i:])
        return prompt

    def _judge_quality(self, candidate: Dict[str, str], task: Dict[str, str]) -> int:
        """Judge the quality of a candidate prompt."""
        # Placeholder for LLM-as-judge logic
        # This is a mock implementation that always returns 80
        return 80

    def produce(self) -> Optional[Dict[str, str]]:
        """Return the next token-golf result and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        task = self._load_task(plugin_dir)

        if not state["active_tokens"]:
            active_prompt = {"prompt": task["baseline_prompt"], "tokens": len(task["baseline_prompt"].split()), "score": 0}
            state["active_tokens"] = active_prompt["tokens"]
            state["baseline_tokens"] = active_prompt["tokens"]
        else:
            active_prompt = self._load_active_prompt(plugin_dir)

        candidates = self._generate_candidates(task, active_prompt)
        for candidate in candidates:
            candidate["score"] = self._judge_quality(candidate, task)

        winner = max(candidates, key=lambda x: (x["score"], -x["tokens"]))
        if winner["score"] >= 80 and winner["tokens"] < active_prompt["tokens"]:
            state["winner"] = winner
            state["active_tokens"] = winner["tokens"]
            self._save_active_prompt(plugin_dir, winner)
        else:
            state["winner"] = None

        state["candidates"] = candidates
        state["plateau_ticks"] += 1 if not state["winner"] else 0
        self._save_state(plugin_dir, state)

        return {
            "tick": len(state["candidates"]),
            "active_tokens": state["active_tokens"],
            "baseline_tokens": state["baseline_tokens"],
            "pct_reduction": ((state["baseline_tokens"] - state["active_tokens"]) / state["baseline_tokens"]) * 100,
            "quality": winner["score"] if state["winner"] else None
        }
