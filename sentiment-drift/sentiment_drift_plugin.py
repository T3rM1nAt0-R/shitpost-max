"""Repeatedly asks the LLM to rate a fixed sentence's sentiment, tracking running mean/variance."""

import re

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

FIXED_SENTENCE = "The weather today is absolutely wonderful and I feel great."
PROMPT = (
    "Rate the sentiment of this sentence from 1 (very negative) to 10 (very positive). "
    "Respond with ONLY the number, nothing else.\n\n"
    f"Sentence: {FIXED_SENTENCE}"
)

_SCORE_RE = re.compile(r"\b([1-9]|10)\b")


def _parse_score(text):
    m = _SCORE_RE.search(text)
    if not m:
        raise ValueError(f"no 1-10 score found in: {text!r}")
    return int(m.group(1))


def _update_stats(state, score):
    n = state["n"] + 1
    delta = score - state["mean"]
    mean = state["mean"] + delta / n
    delta2 = score - mean
    m2 = state["m2"] + delta * delta2
    variance = m2 / n if n > 1 else 0.0
    return {"n": n, "mean": mean, "m2": m2, "variance": variance}


class SentimentDriftPlugin(Shitpost):
    """Emit a sentiment score and running stats each tick. Skips the tick on call failure or unparseable score."""

    name = "sentiment-drift"
    internal = False
    commit_template = "sentiment score {score}, running mean {running_mean}"

    def produce(self):
        try:
            output = _call_ollama(PROMPT)
            score = _parse_score(output)
        except Exception:
            return None

        state = self._load_persisted_state({"n": 0, "mean": 0.0, "m2": 0.0, "variance": 0.0})
        new_state = _update_stats(state, score)
        self._save_persisted_state(new_state)

        return {
            "score": score,
            "running_mean": round(new_state["mean"], 2),
            "running_variance": round(new_state["variance"], 4),
            "sample_count": new_state["n"],
        }
