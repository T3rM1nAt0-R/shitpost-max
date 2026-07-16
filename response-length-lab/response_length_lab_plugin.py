"""Sends a fixed prompt with varying max_tokens (num_predict) limits and records actual response length."""

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

PROMPT = "Write a short story about a robot learning to paint."
MAX_TOKENS_VALUES = [10, 30, 60, 100]


def _measure(text):
    return {"char_count": len(text), "word_count": len(text.split())}


class ResponseLengthLabPlugin(Shitpost):
    """Emit response-length measurements for one MAX_TOKENS_VALUES entry per tick, cycling through the list."""

    name = "response-length-lab"
    internal = False
    commit_template = "response-length(max={requested_max_tokens}): {word_count} words"

    def produce(self):
        state = self._load_persisted_state({"index": 0})
        index = state["index"]
        max_tokens = MAX_TOKENS_VALUES[index]

        try:
            output = _call_ollama(PROMPT, num_predict=max_tokens)
        except Exception:
            return None

        measured = _measure(output)

        result = {
            "requested_max_tokens": max_tokens,
            "char_count": measured["char_count"],
            "word_count": measured["word_count"],
        }

        self._save_persisted_state({"index": (index + 1) % len(MAX_TOKENS_VALUES)})

        return result
