"""Substitutes fixed values into a haiku prompt template and runs each variant through the local LLM."""

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

TEMPLATE = "Write a {adjective} haiku about {subject}."
VARIANTS = [
    ("melancholy", "autumn leaves"),
    ("joyful", "a new puppy"),
    ("mysterious", "an old library"),
    ("energetic", "a thunderstorm"),
    ("peaceful", "a quiet lake"),
]


def _fill(adjective, subject):
    return TEMPLATE.format(adjective=adjective, subject=subject)


class PromptTemplateLabPlugin(Shitpost):
    """Emit an LLM haiku for one VARIANTS entry per tick, cycling through the list. Skips the tick on call failure."""

    name = "prompt-template-lab"
    internal = False
    commit_template = "haiku({adjective}, {subject}) generated"

    def produce(self):
        state = self._load_persisted_state({"index": 0})
        index = state["index"]
        adjective, subject = VARIANTS[index]
        prompt = _fill(adjective, subject)

        try:
            output = _call_ollama(prompt)
        except Exception:
            return None

        result = {
            "adjective": adjective,
            "subject": subject,
            "output": output,
        }

        self._save_persisted_state({"index": (index + 1) % len(VARIANTS)})

        return result
