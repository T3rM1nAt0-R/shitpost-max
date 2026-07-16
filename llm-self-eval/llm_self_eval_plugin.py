"""Asks the LLM to answer a fixed prompt, then rate its own response quality 1-10, tracking a running average."""

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

PROMPTS = [
    "Explain photosynthesis in one sentence.",
    "Write a haiku about autumn.",
    "Give one tip for better sleep.",
]

_RATING_RE = re.compile(r"\b([1-9]|10)\b")


def _parse_rating(text):
    m = _RATING_RE.search(text)
    if not m:
        raise ValueError(f"no 1-10 rating found in: {text!r}")
    return int(m.group(1))


class LlmSelfEvalPlugin(Shitpost):
    """Emit an LLM response plus its own self-rating each tick, cycling through PROMPTS."""

    name = "llm-self-eval"
    internal = False
    commit_template = "self-eval({prompt}): rated {self_rating}/10"

    def produce(self):
        state = self._load_persisted_state({"index": 0, "n": 0, "sum_rating": 0})
        index = state["index"]
        prompt = PROMPTS[index]

        try:
            response = _call_ollama(prompt)
            rating_prompt = (
                f'Rate the quality of this response to the question "{prompt}" '
                "on a scale of 1 (poor) to 10 (excellent). Respond with ONLY the number.\n\n"
                f"Response: {response}"
            )
            rating_text = _call_ollama(rating_prompt)
            rating = _parse_rating(rating_text)
        except Exception:
            return None

        n = state["n"] + 1
        sum_rating = state["sum_rating"] + rating
        running_avg = sum_rating / n

        self._save_persisted_state({
            "index": (index + 1) % len(PROMPTS),
            "n": n,
            "sum_rating": sum_rating,
        })

        return {
            "prompt": prompt,
            "response": response,
            "self_rating": rating,
            "running_avg_rating": round(running_avg, 2),
            "sample_count": n,
        }
