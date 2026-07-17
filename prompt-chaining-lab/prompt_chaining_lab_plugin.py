"""Chains two local LLM calls per tick: stage 1 writes a sentence, stage 2 summarizes it in 3 words."""

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

TOPICS = ["the ocean", "artificial intelligence", "coffee", "mountains", "time travel"]


class PromptChainingLabPlugin(Shitpost):
    """Emit a two-stage LLM chain result per tick, cycling through TOPICS. Skips the tick on any call failure."""

    name = "prompt-chaining-lab"
    internal = False
    commit_template = "chain {topic}: {stage2_output}"

    def produce(self):
        state = self._load_persisted_state({"index": 0})
        index = state["index"]
        topic = TOPICS[index]

        try:
            stage1 = _call_ollama(f"Write exactly one sentence about {topic}.")
            stage2 = _call_ollama(f"Summarize this in exactly 3 words: {stage1}")
        except Exception:
            return None

        result = {
            "topic": topic,
            "stage1_output": stage1,
            "stage2_output": stage2,
        }

        self._save_persisted_state({"index": (index + 1) % len(TOPICS)})

        return result
