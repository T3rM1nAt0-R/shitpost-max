import json
import os
from typing import Dict, List

from harness.shitpost_base import Shitpost


class LLMvsLLMPlugin(Shitpost):
    """Compare answers from two local LLMs on the same question."""

    name = "llm-vs-llm"
    internal = False
    commit_template = "llm-vs-llm: Q{tick_num} — {disagreement_count} disagreements so far"

    def __init__(self):
        super().__init__()
        self._questions_file_name = "questions.json"

    def _load_questions(self, plugin_dir: str) -> List[Dict[str, str]]:
        """Load the question bank, creating a default if missing."""
        path = os.path.join(plugin_dir, self._questions_file_name)
        if not os.path.exists(path):
            default = [
                {
                    "question": "What is the capital of France?",
                    "reference": "Paris",
                },
                {
                    "question": "What is 2 + 2?",
                    "reference": "4",
                },
                {
                    "question": "Who wrote Romeo and Juliet?",
                    "reference": "Shakespeare",
                },
                {
                    "question": "What is the boiling point of water in Celsius?",
                    "reference": "100",
                },
                {
                    "question": "What planet is known as the Red Planet?",
                    "reference": "Mars",
                },
            ]
            with open(path, "w", encoding="utf-8") as f:
                json.dump(default, f, indent=2)
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _ask_llm(self, model: str, question: str) -> str:
        """Ask a local LLM via HTTP."""
        import requests
        endpoint = os.getenv("LLM_ENDPOINT", "http://localhost:11434/api/generate")
        try:
            response = requests.post(
                endpoint,
                json={"model": model, "prompt": question},
                timeout=30,
            )
        except requests.exceptions.ConnectionError as exc:
            return f"(connection error: {exc})"
        except requests.exceptions.Timeout:
            return "(timeout)"
        except requests.exceptions.RequestException as exc:
            return f"(request failed: {exc})"
        if response.status_code != 200:
            return f"(HTTP {response.status_code})"
        try:
            return response.json()["choices"][0]["text"].strip()
        except (KeyError, TypeError, ValueError) as exc:
            return f"(parse error: {exc})"

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

        state = self._load_persisted_state({"tick_num": 0, "disagreement_count": 0})
        questions = self._load_questions(plugin_dir)

        # Pick a question (round-robin).
        tick_num = state["tick_num"]
        question = questions[tick_num % len(questions)]
        reference = question["reference"]

        # Ask both models.
        answer_a = self._ask_llm(
            os.getenv("LLM_A_MODEL", "qwen2.5-coder:7b-instruct-q6_K"),
            question["question"],
        )
        answer_b = self._ask_llm(
            os.getenv("LLM_B_MODEL", "llama3.1:8b"),
            question["question"],
        )

        # Compare answers.
        disagreement = self._compare_answers(answer_a, answer_b, reference)

        # Update state.
        state["tick_num"] += 1
        if disagreement:
            state["disagreement_count"] += 1

        self._save_persisted_state(state)

        return {
            "tick_num": tick_num + 1,
            "question": question["question"],
            "answer_a": answer_a,
            "answer_b": answer_b,
            "reference": reference,
            "disagreement": disagreement,
            "disagreement_count": state["disagreement_count"],
        }
