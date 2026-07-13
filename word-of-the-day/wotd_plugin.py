import json
import os
import random
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen

from harness.shitpost_base import Shitpost


WORDLIST = [
    {"word": "ephemeral", "definition": "lasting for a very short time", "part_of_speech": "adjective"},
    {"word": "ubiquitous", "definition": "present everywhere", "part_of_speech": "adjective"},
    {"word": "serendipity", "definition": "a pleasant surprise found by chance", "part_of_speech": "noun"},
    {"word": "mellifluous", "definition": "sweet-sounding", "part_of_speech": "adjective"},
    {"word": "cacophony", "definition": "a harsh mixture of sounds", "part_of_speech": "noun"},
]


class WordOfTheDayPlugin(Shitpost):
    """Emit one random word from WORDLIST per tick."""

    name = "word-of-the-day"
    internal = False
    commit_template = "wotd: {word}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "word_of_the_day_state.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it at tick 0."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: word of the day state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"tick"}
            if not required.issubset(state.keys()):
                print(
                    "warning: word of the day state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "tick": 0,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API and return the response."""
        url = "http://localhost:1601/api/generate"
        headers = {"Content-Type": "application/json"}
        data = json.dumps({"model": "qwen2.5-coder:7b-instruct-q6_K", "prompt": prompt, "stream": False}).encode("utf-8")
        req = Request(url, headers=headers, data=data)
        with urlopen(req) as response:
            result = response.read()
        return json.loads(result)["response"]

    def produce(self) -> dict:
        """Return a random word from WORDLIST and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Pick a random entry from WORDLIST
        word_entry = random.choice(WORDLIST)
        word = word_entry["word"]
        definition = word_entry["definition"]
        part_of_speech = word_entry["part_of_speech"]

        prompt = f"Write a short sentence using the word '{word}' (meaning: {definition})."
        try:
            example = self._call_ollama(prompt)
        except Exception as e:
            print(f"warning: Ollama API call failed ({e}); falling back to template", file=sys.stderr)
            example = f"The {word} was unexpected."
            source = "template"
        else:
            example = example.strip()
            source = "ollama"

        state["tick"] += 1
        self._save_state(plugin_dir, state)

        return {
            "tick": state["tick"],
            "word": word,
            "definition": definition,
            "pos": part_of_speech,
            "example": example,
            "source": source,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
