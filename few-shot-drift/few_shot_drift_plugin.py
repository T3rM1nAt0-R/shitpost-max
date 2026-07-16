"""Measures how LLM sentiment classification changes as the number of few-shot examples varies."""

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

EXAMPLES = [
    ("This movie was fantastic!", "positive"),
    ("I hated every minute of it.", "negative"),
    ("It was okay, nothing special.", "neutral"),
]
TEST_SENTENCE = "The service was surprisingly good."
SHOT_COUNTS = [0, 1, 2, 3]


def _build_prompt(shot_count):
    prefix = ""
    for text, sentiment in EXAMPLES[:shot_count]:
        prefix += f"Text: {text}\nSentiment: {sentiment}\n\n"
    return prefix + f"Text: {TEST_SENTENCE}\nSentiment:"


class FewShotDriftPlugin(Shitpost):
    """Emit LLM output for one shot_count per tick, cycling through SHOT_COUNTS. Skips the tick on call failure."""

    name = "few-shot-drift"
    internal = False
    commit_template = "few-shot({shot_count}): {output}"

    def produce(self):
        state = self._load_persisted_state({"index": 0})
        index = state["index"]
        shot_count = SHOT_COUNTS[index]
        prompt = _build_prompt(shot_count)

        try:
            output = _call_ollama(prompt)
        except Exception:
            return None

        result = {
            "shot_count": shot_count,
            "output": output,
        }

        self._save_persisted_state({"index": (index + 1) % len(SHOT_COUNTS)})

        return result
