"""Presents fixed arithmetic/logic problems zero-shot and tracks a running correct/total count."""

import json
import urllib.request

OLLAMA_URL = "http://localhost:1601/api/generate"
MODEL = "qwen2.5-coder:7b-instruct-q6_K"


def _call_ollama(prompt, num_predict=None):
    payload = {"model": MODEL, "prompt": prompt, "stream": False}
    if num_predict is not None:
        payload["options"] = {"num_predict": num_predict}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as response:
        result = json.loads(response.read())
    return result["response"].strip()

from harness.shitpost_base import Shitpost

QUESTIONS = [
    ("What is 17 + 28?", "45"),
    ("If all cats are mammals and Felix is a cat, is Felix a mammal? Answer yes or no.", "yes"),
    ("What is 9 times 7?", "63"),
    ("Is 2 greater than 5? Answer yes or no.", "no"),
    ("What is 100 divided by 4?", "25"),
]


def _is_correct(answer, expected):
    return expected.lower() in answer.lower().strip()


class ZeroShotBenchPlugin(Shitpost):
    """Emit a zero-shot benchmark result per tick, cycling through QUESTIONS. Skips the tick on call failure."""

    name = "zero-shot-bench"
    internal = False
    commit_template = "zero-shot: {running_correct}/{running_total} correct"

    def produce(self):
        state = self._load_persisted_state({"index": 0, "correct": 0, "total": 0})
        index = state["index"]
        question, expected = QUESTIONS[index]
        prompt = f"{question} Answer with ONLY the final answer, no explanation."

        try:
            answer = _call_ollama(prompt)
        except Exception:
            return None

        correct = _is_correct(answer, expected)
        new_total = state["total"] + 1
        new_correct = state["correct"] + (1 if correct else 0)

        self._save_persisted_state({
            "index": (index + 1) % len(QUESTIONS),
            "correct": new_correct,
            "total": new_total,
        })

        return {
            "question": question,
            "answer": answer,
            "correct": correct,
            "running_correct": new_correct,
            "running_total": new_total,
        }
