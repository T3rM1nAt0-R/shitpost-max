import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class AnagramHunterPlugin(Shitpost):
    """Scan a wordlist for anagrams and emit the largest set found."""

    name = "anagram-hunter"
    internal = False
    commit_template = "anagram: {word1} <-> {word2}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "anagram_state.json"
        self._logged_sigs_file_name = "logged_sigs.json"
        self._words_file_name = "words.txt"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it at tick 0."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: anagram state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"tick", "word_length"}
            if not required.issubset(state.keys()):
                print(
                    "warning: anagram state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "tick": 0,
            "word_length": 2,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _load_logged_sigs(self, plugin_dir: str) -> set:
        """Load the set of logged anagram signatures."""
        path = os.path.join(plugin_dir, self._logged_sigs_file_name)
        if not os.path.exists(path):
            return set()

        try:
            with open(path, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except json.JSONDecodeError as exc:
            print(
                f"warning: logged signatures file is corrupt ({exc}); starting fresh",
                file=sys.stderr,
            )
            return set()

    def _save_logged_sigs(self, plugin_dir: str, logged_sigs: set) -> None:
        path = os.path.join(plugin_dir, self._logged_sigs_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(list(logged_sigs), f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _load_words(self, plugin_dir: str) -> list:
        """Load the wordlist."""
        path = os.path.join(plugin_dir, self._words_file_name)
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    def _build_sorted_letter_index(self, words: list) -> dict:
        """Build a sorted-letter index of words."""
        index = {}
        for word in words:
            key = "".join(sorted(word))
            if key not in index:
                index[key] = []
            index[key].append(word)
        return index

    def _find_best_anagram_set(self, index: dict, logged_sigs: set) -> tuple:
        """Find the largest anagram set that hasn't been logged."""
        best_set = None
        for key, words in index.items():
            if len(words) < 2 or any(sig == key for sig in logged_sigs):
                continue
            if not best_set or len(words) > len(best_set[1]):
                best_set = (key, words)
        return best_set

    def produce(self) -> dict:
        """Return the largest anagram set and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        logged_sigs = self._load_logged_sigs(plugin_dir)
        words = self._load_words(plugin_dir)
        index = self._build_sorted_letter_index(words)

        tick = state["tick"]
        word_length = state["word_length"]

        best_set = None
        for key, words in index.items():
            if len(key) != word_length:
                continue
            if not any(sig == key for sig in logged_sigs):
                if not best_set or len(words) > len(best_set[1]):
                    best_set = (key, words)

        if best_set:
            anagram_set, words = best_set
            signature = "".join(sorted(anagram_set))
            if signature not in logged_sigs:
                logged_sigs.add(signature)
                state["tick"] += 1
                state["word_length"] += 1

                self._save_state(plugin_dir, state)
                self._save_logged_sigs(plugin_dir, logged_sigs)

                return {
                    "tick": state["tick"],
                    "word_length": word_length,
                    "anagram_set": words,
                    "set_size": len(words),
                    "signature": signature,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

        return None
