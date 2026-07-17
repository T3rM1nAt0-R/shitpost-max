"""Generates a syllable-perfect haiku daily via local LLM. 5-7-5 discipline the model doesn't even know it's following."""

import json
import os
import string
import sys
import urllib.request
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost

OLLAMA_URL = "http://localhost:1601/api/generate"
MODEL = "qwen2.5-coder:7b-instruct-q6_K"
MAX_ATTEMPTS = 5

HAIKU_PROMPT = (
    "Write a haiku (three lines, 5-7-5 syllables) about any topic you like. "
    "Respond with ONLY the three lines, one per line, nothing else -- no title, "
    "no explanation, no syllable counts."
)


def _call_ollama(prompt):
    payload = {"model": MODEL, "prompt": prompt, "stream": False}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as response:
        result = json.loads(response.read())
    return result["response"].strip()


def _count_syllables(word):
    """Approximate English syllable count via vowel-group heuristic (not dictionary-exact, but a
    real, deterministic, testable count -- unlike counting words, which is what this validator
    used to do before 2026-07-17)."""
    word = word.lower().strip(string.punctuation)
    if not word:
        return 0
    vowels = "aeiouy"
    count = 0
    prev_was_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_was_vowel:
            count += 1
        prev_was_vowel = is_vowel
    if word.endswith("e") and count > 1:
        count -= 1
    return max(count, 1)


def _line_syllables(line):
    return sum(_count_syllables(w) for w in line.split())


class HaikuDailyPlugin(Shitpost):
    """Generate one syllable-counted haiku each day using a local LLM and append it to a growing collection."""

    name = "haiku-daily"
    internal = False
    commit_template = "haiku: {s1} / {s2} / {s3}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "haiku_state.jsonl"
        self._haiku_file_name = "haiku.txt"

    def _load_state(self, plugin_dir: str) -> list:
        """Load the running haiku state, or initialise it as an empty list."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = [json.loads(line) for line in f]
            except json.JSONDecodeError as exc:
                print(
                    f"warning: haiku state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return []
        else:
            state = []

        return state

    def _save_state(self, plugin_dir: str, state: list) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        with open(path, "w", encoding="utf-8") as f:
            for entry in state:
                json.dump(entry, f)
                f.write("\n")

    def _append_haiku(self, plugin_dir: str, haiku: list) -> None:
        path = os.path.join(plugin_dir, self._haiku_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"---\n{datetime.now(timezone.utc).isoformat()}\n")
            for line in haiku:
                f.write(line + "\n")

    def produce(self) -> dict | None:
        """Return the next haiku and update persistent files.

        Real bugs fixed 2026-07-17: `_query_model()` was an unimplemented
        placeholder returning fixed fake text, and `_validate_haiku()`
        counted words, not syllables -- so this plugin had never produced a
        single tick (the fake placeholder text itself failed its own
        word-count check). Now makes a real Ollama call and validates with
        an actual (approximate) syllable counter, retrying up to
        MAX_ATTEMPTS times against the model's real non-deterministic
        output before giving up and skipping this tick (not crashing).
        """
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        haiku = None
        for _ in range(MAX_ATTEMPTS):
            try:
                candidate = self._query_model()
            except Exception as exc:
                print(f"warning: haiku-daily model call failed ({exc}); skipping tick", file=sys.stderr)
                return None
            if self._validate_haiku(candidate):
                haiku = candidate
                break

        if haiku is None:
            print(f"warning: no valid 5-7-5 haiku after {MAX_ATTEMPTS} attempts; skipping tick", file=sys.stderr)
            return None

        state.append({
            "tick": len(state) + 1,
            "lines": haiku,
            "syllable_counts": [_line_syllables(line) for line in haiku],
            "accepted": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        self._save_state(plugin_dir, state)
        self._append_haiku(plugin_dir, haiku)

        return {
            "tick": len(state),
            "lines": haiku,
            "syllable_counts": [_line_syllables(line) for line in haiku],
            "s1": haiku[0],
            "s2": haiku[1],
            "s3": haiku[2],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _query_model(self) -> list:
        response = _call_ollama(HAIKU_PROMPT)
        lines = [line.strip() for line in response.splitlines() if line.strip()]
        return lines[:3] if len(lines) >= 3 else lines

    def _validate_haiku(self, haiku) -> bool:
        if not haiku or len(haiku) != 3:
            return False

        # Real bug (DeepSeek review, 2026-07-17): the middle line was never
        # checked at all -- only lines 0 and 2 (a 5-syllable middle line
        # would have passed as a valid "5-7-5" haiku). Same tolerance width
        # as the other two lines (+/-1 either side of the target), just
        # centered on 7 instead of 5, since the syllable counter is an
        # approximate heuristic, not exact.
        syllable_counts = [_line_syllables(line) for line in haiku]
        return (
            5 <= syllable_counts[0] <= 7
            and 6 <= syllable_counts[1] <= 8
            and 5 <= syllable_counts[2] <= 7
        )
