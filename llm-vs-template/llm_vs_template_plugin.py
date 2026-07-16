"""Compares LLM output about a fixed topic to a fixed hand-written template sentence via word-overlap similarity."""

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

TOPICS = [
    ("the ocean", "The ocean covers most of the Earth and is full of life."),
    ("coffee", "Coffee is a popular drink made from roasted beans."),
    ("mountains", "Mountains are tall landforms that rise sharply from the surrounding land."),
]


def _jaccard(text_a, text_b):
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    if not words_a and not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


class LlmVsTemplatePlugin(Shitpost):
    """Emit an LLM-vs-template similarity score for one TOPICS entry per tick, cycling through the list."""

    name = "llm-vs-template"
    internal = False
    commit_template = "llm-vs-template({topic}): {similarity} similarity"

    def produce(self):
        state = self._load_persisted_state({"index": 0})
        index = state["index"]
        topic, template_sentence = TOPICS[index]

        try:
            llm_output = _call_ollama(f"Write exactly one sentence about {topic}.")
        except Exception:
            return None

        similarity = _jaccard(llm_output, template_sentence)

        result = {
            "topic": topic,
            "llm_output": llm_output,
            "template_sentence": template_sentence,
            "similarity": round(similarity, 3),
        }

        self._save_persisted_state({"index": (index + 1) % len(TOPICS)})

        return result
