"""Reports a fixed embedded list of function cyclomatic complexity scores, sorted highest-first, cycling."""

from harness.shitpost_base import Shitpost

SCORES = [
    ("handle_request", 14),
    ("validate_input", 9),
    ("parse_config", 6),
    ("main", 3),
    ("helper", 1),
]
SORTED = sorted(SCORES, key=lambda s: -s[1])


class CodeComplexityWatchPlugin(Shitpost):
    """Emit one SORTED entry per tick, cycling through the list."""

    name = "code-complexity-watch"
    internal = False
    commit_template = "complexity {function}: {complexity}"

    def produce(self) -> dict:
        state = self._load_persisted_state({"index": 0})
        index = state["index"]

        func, score = SORTED[index]

        result = {
            "function": func,
            "complexity": score,
        }

        self._save_persisted_state({"index": (index + 1) % len(SORTED)})

        return result
