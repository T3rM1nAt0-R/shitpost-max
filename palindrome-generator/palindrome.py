import json
import os
import re
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen

from harness.shitpost_base import Shitpost


class PalindromeGenerator(Shitpost):
    """Generate a palindrome at least `target` characters long."""

    name = "palindrome-generator"
    internal = False
    commit_template = "palindrome attempt: accepted={accepted}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "palindrome_state.json"
        self._record_file_name = "record.txt"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it at target=10 and tick=0."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: palindrome state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"target", "tick"}
            if not required.issubset(state.keys()):
                print(
                    "warning: palindrome state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "target": 10,
            "tick": 0,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

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

        state = self._load_state(plugin_dir)

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

        self._save_state(plugin_dir, state)

        return {
            "tick": tick,
            "palindrome": raw_output,
            "length": length if is_valid else 0,
            "target": state["target"],
            "accepted": is_valid,
        }
