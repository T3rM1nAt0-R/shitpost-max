"""Generates palindromes of arbitrary length, because some sentences deserve to read the same backwards. Racecar. Always racecar."""

import json
import os
import re
from urllib.request import Request, urlopen

from harness.shitpost_base import Shitpost


class PalindromeGenerator(Shitpost):
    """Generate a palindrome at least `target` characters long."""

    name = "palindrome-generator"
    internal = False
    commit_template = "palindrome attempt: accepted={accepted}"

    def __init__(self):
        super().__init__()
        self._record_file_name = "record.txt"

    def _persisted_state_path(self) -> str:
        """Preserve the original custom filename so existing state is not lost."""
        return os.path.join(self._plugin_dir(), "palindrome_state.json")

    def _append_record(self, plugin_dir: str, length: int, raw_output: str) -> None:
        path = os.path.join(plugin_dir, self._record_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{length}|{raw_output}\n")

    def _is_valid_palindrome(self, s: str) -> bool:
        cleaned = re.sub(r'[^a-zA-Z0-9]', '', s).lower()
        return cleaned == cleaned[::-1] if cleaned else False

    def _call_ollama(self, prompt: str) -> str:
        url = "http://localhost:1601/api/generate"
        headers = {
            "Content-Type": "application/json",
        }
        data = json.dumps({"model": "qwen2.5-coder:7b-instruct-q6_K", "prompt": prompt, "stream": False}).encode("utf-8")
        req = Request(url, headers=headers, data=data)
        with urlopen(req) as response:
            result = response.read().decode("utf-8")
        return json.loads(result)["response"]

    def produce(self) -> dict:
        """Generate a palindrome and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({"target": 10, "tick": 0})

        target = state["target"]
        tick = state["tick"] + 1
        state["tick"] = tick

        prompt = f"Generate a palindrome at least {target} characters long."
        raw_output = self._call_ollama(prompt)
        is_valid = self._is_valid_palindrome(raw_output)

        if is_valid:
            length = len(re.sub(r'[^a-zA-Z0-9]', '', raw_output).lower())
            state["target"] += 5
            self._append_record(plugin_dir, length, raw_output)

        self._save_persisted_state(state)

        return {
            "tick": tick,
            "palindrome": raw_output,
            "length": length if is_valid else 0,
            "target": state["target"],
            "accepted": is_valid,
        }
