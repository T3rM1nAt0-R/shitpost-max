import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class HallucinationWitnessPlugin(Shitpost):
    """Daily tick that asks a local LLM a factual question with a known, verifiable answer, then scores whether the answer is correct, hallucinated, or refused."""

    name = "hallucination-witness"
    internal = False
    commit_template = "hallucination-witness: {verdict} — {acc_30:.0%} 30d, {acc_all:.0%} all"

    def __init__(self):
        super().__init__()
        self._state_file_name = "state.jsonl"
        self._summary_file_name = "summary.json"
        self._facts = [
            {"id": 1, "question": "What is the capital of France?", "answer": "Paris", "category": "geography", "source": "https://en.wikipedia.org/wiki/France"},
            # Add more facts here...
        ]

    def _load_state(self, plugin_dir: str) -> list:
        """Load the running state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = [json.loads(line.strip()) for line in f]
            except json.JSONDecodeError as exc:
                print(
                    f"warning: state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return []
        else:
            state = []

        return state

    def _save_state(self, plugin_dir: str, state: list) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            for entry in state:
                json.dump(entry, f)
                f.write("\n")
        os.replace(tmp_path, path)

    def _load_summary(self, plugin_dir: str) -> dict:
        """Load the running summary."""
        path = os.path.join(plugin_dir, self._summary_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    summary = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: summary file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return {"acc_30": 0.0, "acc_90": 0.0, "acc_all": 0.0, "total_ticks": 0}
        else:
            summary = {"acc_30": 0.0, "acc_90": 0.0, "acc_all": 0.0, "total_ticks": 0}

        return summary

    def _save_summary(self, plugin_dir: str, summary: dict) -> None:
        path = os.path.join(plugin_dir, self._summary_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(summary, f)
            f.write("\n")
        os.replace(tmp_path, path)

    def _judge_answer(self, model_answer: str, reference_answer: str) -> str:
        """Judge the answer using an LLM-as-judge prompt."""
        judge_prompt = f"Does answer '{model_answer}' mean the same as reference '{reference_answer}'? Answer only YES/NO/PARTIAL."
        # Simulate calling the judge model here
        if model_answer.strip().lower() == reference_answer.strip().lower():
            return "YES"
        elif model_answer.strip().lower() in reference_answer.strip().lower():
            return "PARTIAL"
        else:
            return "NO"

    def produce(self) -> dict:
        """Return the result of asking a question and scoring the answer."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        summary = self._load_summary(plugin_dir)

        # Pick a question round-robin
        tick = len(state) + 1
        question_id = (tick - 1) % len(self._facts)
        fact = self._facts[question_id]

        # Simulate calling the model here
        model_answer = "Paris"  # Replace with actual model call

        verdict = self._judge_answer(model_answer, fact["answer"])
        if verdict == "YES":
            accuracy_30 = summary.get("acc_30", 1.0)
            accuracy_90 = summary.get("acc_90", 1.0)
            accuracy_all = summary.get("acc_all", 1.0)
            summary["acc_30"] = (accuracy_30 * (tick - 1) + 1) / tick
            summary["acc_90"] = (accuracy_90 * (tick - 1) + 1) / tick
            summary["acc_all"] = (accuracy_all * (tick - 1) + 1) / tick
        elif verdict == "NO":
            accuracy_30 = summary.get("acc_30", 0.0)
            accuracy_90 = summary.get("acc_90", 0.0)
            accuracy_all = summary.get("acc_all", 0.0)
            summary["acc_30"] = (accuracy_30 * (tick - 1) + 0) / tick
            summary["acc_90"] = (accuracy_90 * (tick - 1) + 0) / tick
            summary["acc_all"] = (accuracy_all * (tick - 1) + 0) / tick

        summary["total_ticks"] = tick

        state.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question_id": fact["id"],
            "question": fact["question"],
            "answer": model_answer,
            "reference": fact["answer"],
            "verdict": verdict,
            "category": fact["category"]
        })

        self._save_state(plugin_dir, state)
        self._save_summary(plugin_dir, summary)

        return {
            "tick": tick,
            "question_id": question_id,
            "question": fact["question"],
            "answer": model_answer,
            "reference": fact["answer"],
            "verdict": verdict,
            "category": fact["category"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
