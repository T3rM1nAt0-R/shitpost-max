"""Tracks LLM response confidence via self-consistency across 3 repeated samples of a fixed question.

Ollama does not expose real per-token log probabilities for this model via
either its native or OpenAI-compatible endpoint (confirmed 2026-07-16) --
this is a deliberate, documented substitution: agreement rate across
repeated samples of the same question, a real confidence signal used in
LLM eval literature, not a fake logprobs number.
"""

from collections import Counter

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

FIXED_QUESTION = "What is the capital of Japan? Answer with ONLY the city name."
SAMPLES = 3


def _normalize(text):
    return text.strip().lower().rstrip(".")


def _agreement_fraction(answers):
    counts = Counter(_normalize(a) for a in answers)
    return counts.most_common(1)[0][1] / len(answers)


class LogprobsTrackerPlugin(Shitpost):
    """Emit a self-consistency confidence score and running average each tick. Skips the tick if any sample fails."""

    name = "logprobs-tracker"
    internal = False
    commit_template = "self-consistency confidence: {confidence}"

    def produce(self):
        try:
            answers = [_call_ollama(FIXED_QUESTION) for _ in range(SAMPLES)]
        except Exception:
            return None

        confidence = _agreement_fraction(answers)

        state = self._load_persisted_state({"n": 0, "sum_confidence": 0.0})
        n = state["n"] + 1
        sum_confidence = state["sum_confidence"] + confidence
        running_avg = sum_confidence / n
        self._save_persisted_state({"n": n, "sum_confidence": sum_confidence})

        return {
            "answers": answers,
            "confidence": round(confidence, 2),
            "running_avg_confidence": round(running_avg, 4),
            "sample_count": n,
        }
