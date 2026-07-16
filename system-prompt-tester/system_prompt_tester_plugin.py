"""Sends the same fixed user message with varying system prompts to the local LLM's chat endpoint."""

import json
import urllib.request

from harness.shitpost_base import Shitpost

OLLAMA_CHAT_URL = "http://localhost:1601/api/chat"
MODEL = "qwen2.5-coder:7b-instruct-q6_K"

USER_MESSAGE = "What should I have for dinner?"
SYSTEM_PROMPTS = [
    "You are a pirate.",
    "You are an extremely formal butler.",
    "You are an enthusiastic fitness coach.",
    "You are a deadpan comedian.",
]


def _call_chat(system_prompt, user_message):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(OLLAMA_CHAT_URL, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as response:
        result = json.loads(response.read())
    return result["message"]["content"].strip()


class SystemPromptTesterPlugin(Shitpost):
    """Emit an LLM chat response for one SYSTEM_PROMPTS entry per tick, cycling through the list."""

    name = "system-prompt-tester"
    internal = False
    commit_template = "system-prompt-test [{system_prompt}]"

    def produce(self):
        state = self._load_persisted_state({"index": 0})
        index = state["index"]
        system_prompt = SYSTEM_PROMPTS[index]

        try:
            output = _call_chat(system_prompt, USER_MESSAGE)
        except Exception:
            return None

        result = {
            "system_prompt": system_prompt,
            "output": output,
        }

        self._save_persisted_state({"index": (index + 1) % len(SYSTEM_PROMPTS)})

        return result
