#!/usr/bin/env python3

import json
import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class DiffEnginePlugin(Shitpost):
    """Apply a hand-rolled text diff algorithm to a pair of sample texts and commit the resulting diff output."""

    name = "diff-engine"
    internal = False
    commit_template = "diff-engine: \"{pair_name}\" — {edits} edits ({inserts} insertions, {deletes} deletions)"

    def __init__(self):
        super().__init__()
        self._state_file_name = "state.jsonl"
        self._samples_dir = "samples"
        self._sample_pairs = [
            ("poem_old.txt", "poem_new.txt"),
            ("config_old.txt", "config_new.txt"),
            ("code_old.py", "code_new.py")
        ]
        self._current_pair_index = 0

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it at the first sample pair."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    states = [json.loads(line) for line in f]
            except json.JSONDecodeError as exc:
                print(
                    f"warning: state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"timestamp", "pair_name", "lines_a", "lines_b", "edits", "inserts", "deletes"}
            if not all(required.issubset(state.keys()) for state in states):
                print(
                    "warning: state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return states[-1]

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "timestamp": None,
            "pair_name": None,
            "lines_a": [],
            "lines_b": [],
            "edits": 0,
            "inserts": 0,
            "deletes": 0
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            for line in json.dumps(state).splitlines():
                f.write(line + "\n")
        os.replace(tmp_path, path)

    def _load_sample_texts(self, plugin_dir: str) -> tuple:
        pair = self._sample_pairs[self._current_pair_index]
        with open(os.path.join(plugin_dir, self._samples_dir, pair[0]), "r", encoding="utf-8") as f:
            lines_a = f.readlines()
        with open(os.path.join(plugin_dir, self._samples_dir, pair[1]), "r", encoding="utf-8") as f:
            lines_b = f.readlines()
        return lines_a, lines_b

    def _myers_diff(self, lines_a: list, lines_b: list) -> dict:
        # Placeholder for the actual Myers diff algorithm implementation
        edits = len(lines_a) + len(lines_b)
        inserts = len(lines_b)
        deletes = len(lines_a)
        return {
            "edits": edits,
            "inserts": inserts,
            "deletes": deletes
        }

    def _format_diff(self, pair_name: str, lines_a: list, lines_b: list) -> str:
        # Placeholder for the actual unified-diff formatter implementation
        diff = f"--- a/{pair_name}_old\n+++ b/{pair_name}_new\n@@ -1,0 +1,{len(lines_b)} @@\n"
        for line in lines_b:
            diff += "+ " + line.strip() + "\n"
        return diff

    def produce(self) -> dict:
        """Return the diff output and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        lines_a, lines_b = self._load_sample_texts(plugin_dir)

        diff_result = self._myers_diff(lines_a, lines_b)
        diff_output = self._format_diff("sample", lines_a, lines_b)

        state["timestamp"] = datetime.now(timezone.utc).isoformat()
        state["pair_name"] = "sample"
        state["lines_a"] = lines_a
        state["lines_b"] = lines_b
        state["edits"] = diff_result["edits"]
        state["inserts"] = diff_result["inserts"]
        state["deletes"] = diff_result["deletes"]

        self._save_state(plugin_dir, state)

        return {
            "timestamp": state["timestamp"],
            "pair_name": state["pair_name"],
            "lines_a": state["lines_a"],
            "lines_b": state["lines_b"],
            "edits": state["edits"],
            "inserts": state["inserts"],
            "deletes": state["deletes"]
        }
