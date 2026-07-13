import json
import os
import random
import re
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class RegexOfTheDayPlugin(Shitpost):
    """Generate a random regular expression and test cases."""

    name = "regex-of-the-day"
    internal = False
    commit_template = "regex-of-the-day: /{pattern}/ — match={match_test} ({match_ok}), nonmatch={nonmatch_test} ({nonmatch_ok})"

    def __init__(self):
        super().__init__()
        self._log_file_name = "regex_of_the_day_log.jsonl"

    def _log_result(self, plugin_dir: str, pattern: str, match_test: str, nonmatch_test: str, match_ok: bool, nonmatch_ok: bool) -> None:
        path = os.path.join(plugin_dir, self._log_file_name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "pattern": pattern,
                "match_test": match_test,
                "nonmatch_test": nonmatch_test,
                "match_ok": match_ok,
                "nonmatch_ok": nonmatch_ok,
            }) + "\n")

    def produce(self) -> dict:
        """Generate a regex and test cases, then log the result."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "pattern": "",
            "match_test": "",
            "nonmatch_test": "",
            "tick": 0,
        })

        # Generate a random regex
        pattern = self._generate_regex()

        # Generate matching and non-matching test cases
        match_test, nonmatch_test = self._generate_tests(pattern)
        match_ok = re.fullmatch(pattern, match_test) is not None
        nonmatch_ok = re.fullmatch(pattern, nonmatch_test) is None

        state["pattern"] = pattern
        state["match_test"] = match_test
        state["nonmatch_test"] = nonmatch_test
        state["tick"] += 1

        self._save_persisted_state(state)
        self._log_result(plugin_dir, pattern, match_test, nonmatch_test, match_ok, nonmatch_ok)

        return {
            "tick": state["tick"],
            "pattern": pattern,
            "match_test": match_test,
            "nonmatch_test": nonmatch_test,
            "match_ok": match_ok,
            "nonmatch_ok": nonmatch_ok,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _generate_regex(self) -> str:
        """Generate a random regex pattern."""
        depth = 0
        max_depth = 4

        def generate_node():
            if random.random() < 0.5 or depth >= max_depth:
                return generate_literal()
            elif random.random() < 0.3:
                return f"({self._generate_regex()}|{self._generate_regex()})"
            elif random.random() < 0.2:
                return f"{self._generate_regex()}*"
            elif random.random() < 0.1:
                return f"{self._generate_regex()}?"
            else:
                return f"{self._generate_regex()}+"

        def generate_literal():
            nonlocal depth
            depth += 1
            result = chr(random.randint(97, 122))
            depth -= 1
            return result

        return generate_node()

    def _generate_tests(self, pattern: str) -> tuple:
        """Generate a matching and a non-matching test case."""
        match_test = self._generate_matching_test(pattern)
        nonmatch_test = self._generate_nonmatching_test(pattern)

        while re.fullmatch(pattern, nonmatch_test) is not None:
            nonmatch_test = self._flip_one_character(nonmatch_test)

        return match_test, nonmatch_test

    def _generate_matching_test(self, pattern: str) -> str:
        """Generate a matching test case."""
        stack = [pattern]
        result = ""

        while stack:
            node = stack.pop()
            if isinstance(node, str):
                result += node
            elif isinstance(node, tuple):
                for subnode in reversed(node):
                    stack.append(subnode)

        return result

    def _generate_nonmatching_test(self, pattern: str) -> str:
        """Generate a non-matching test case."""
        match_test = self._generate_matching_test(pattern)
        return self._flip_one_character(match_test)

    @staticmethod
    def _flip_one_character(s: str) -> str:
        """Flip one character in the string."""
        if not s:
            return s

        index = random.randint(0, len(s) - 1)
        if s[index].isalpha():
            new_char = chr((ord(s[index]) - 97 + 1) % 26 + 97)
        else:
            new_char = str(random.randint(0, 9))

        return s[:index] + new_char + s[index+1:]
