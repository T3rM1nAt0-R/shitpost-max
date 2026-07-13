import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict

from harness.shitpost_base import Shitpost


class LLMvsLLMPlugin(Shitpost):
    """Compare answers from two local LLMs on the same question."""

    name = "llm-vs-llm"
    internal = False
    commit_template = "llm-vs-llm: Q{tick_num} — {disagreement_count} disagreements so far"

    def __init__(self):
        super().__init__()
        self._state_file_name = "llm_vs_llm_state.json"
        self._questions_file_name = "questions.json"

    def _load_state(self, plugin_dir: str) -> Dict[str, any]:
        """Load the running state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: llm-vs-llm state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"tick_num", "disagreement_count"}
            if not required.issubset(state.keys()):
                print(
                    "warning: llm-vs-llm state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> Dict[str, any]:
        return {
            "tick_num": 0,
            "disagreement_count": 0,
        }

    def _save_state(self, plugin_dir: str, state: Dict[str, any]) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _load_questions(self, plugin_dir: str) -> List[Dict[str, str]]:
        """Load the question bank."""
        path = os.path.join(plugin_dir, self._questions_file_name)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _ask_llm(self, model: str, question: str) -> str:
        """Ask a local LLM via HTTP."""
        import requests
        response = requests.post(
            os.getenv("LLM_ENDPOINT"),
            json={"model": model, "prompt": question},
            timeout=30,
        )
        if response.status_code != 200:
            raise Exception(f"Failed to ask {model}: {response.text}")
        return response.json()["choices"][0]["text"].strip()

    def _compare_answers(self, answer_a: str, answer_b: str, reference: str) -> bool:
        """Compare answers with exact match and semantic similarity."""
        if answer_a == answer_b:
            return False
        # Simple heuristic: check if the reference is in either answer.
        if reference in answer_a or reference in answer_b:
            return True
        return False

    def produce(self) -> Dict[str, any]:
        """Return the comparison result and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        questions = self._load_questions(plugin_dir)

        # Pick a question (round-robin).
        tick_num = state["tick_num"]
        question = questions[tick_num % len(questions)]
        reference = question["reference"]

        # Ask both models.
        answer_a = self._ask_llm(os.getenv("LLM_A_MODEL"), question["question"])
        answer_b = self._ask_llm(os.getenv("LLM_B_MODEL"), question["question"])

        # Compare answers.
        disagreement = self._compare_answers(answer_a, answer_b, reference)

        # Update state.
        state["tick_num"] += 1
        if disagreement:
            state["disagreement_count"] += 1

        self._save_state(plugin_dir, state)

        return {
            "tick_num": tick_num + 1,
            "question": question["question"],
            "answer_a": answer_a,
            "answer_b": answer_b,
            "reference": reference,
            "disagreement": disagreement,
            "disagreement_count": state["disagreement_count"],
        }
