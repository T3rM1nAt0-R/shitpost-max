"""Scans fixed embedded source snippets for TODO/FIXME/HACK/XXX markers, cycling through files."""

import re

from harness.shitpost_base import Shitpost

FILES = [
    ("auth.py", "def login(user):\n    # TODO: add rate limiting\n    # TODO: hash passwords properly\n    # FIXME: this leaks timing info\n    return True\n"),
    ("utils.py", "def helper():\n    # HACK: workaround for upstream bug\n    # XXX: remove this before v2\n    return 42\n"),
    ("models.py", "class User:\n    def __init__(self, name):\n        self.name = name\n"),
]

_MARKER_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b")


def _count_markers(text):
    counts = {"TODO": 0, "FIXME": 0, "HACK": 0, "XXX": 0}
    for m in _MARKER_RE.finditer(text):
        counts[m.group(1)] += 1
    return counts


class TodoScannerPlugin(Shitpost):
    """Emit marker counts for one FILES entry per tick, cycling through the list."""

    name = "todo-scanner"
    internal = False
    commit_template = "todo-scan {filename}: {total} markers"

    def produce(self) -> dict:
        state = self._load_persisted_state({"index": 0})
        index = state["index"]

        filename, content = FILES[index]
        counts = _count_markers(content)
        total = sum(counts.values())

        result = {
            "filename": filename,
            "counts": counts,
            "total": total,
        }

        self._save_persisted_state({"index": (index + 1) % len(FILES)})

        return result
