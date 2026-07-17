"""Generates a changelog entry from a fixed embedded commit list, grouped by conventional-commit type, cycling through releases."""

from harness.shitpost_base import Shitpost

RELEASES = [
    ("v1.2.0", ["feat: add dark mode", "fix: login redirect loop", "chore: bump deps"]),
    ("v1.3.0", ["feat: export to CSV", "feat: keyboard shortcuts", "fix: crash on empty input"]),
    ("v1.4.0", ["fix: timezone bug", "chore: update readme", "docs: fix typo"]),
]
KNOWN_TYPES = ["feat", "fix", "chore", "docs"]


def _group(messages):
    buckets = {k: [] for k in KNOWN_TYPES}
    buckets["other"] = []
    for msg in messages:
        if ": " in msg:
            prefix, rest = msg.split(": ", 1)
        else:
            prefix, rest = None, msg
        if prefix in KNOWN_TYPES:
            buckets[prefix].append(rest)
        else:
            buckets["other"].append(msg)
    return buckets


class ChangelogGenPlugin(Shitpost):
    """Emit grouped changelog for one RELEASES entry per tick, cycling through the list."""

    name = "changelog-gen"
    internal = False
    commit_template = "changelog {version} generated"

    def produce(self) -> dict:
        state = self._load_persisted_state({"index": 0})
        index = state["index"]

        version, messages = RELEASES[index]
        grouped = _group(messages)

        result = {
            "version": version,
            "grouped": grouped,
        }

        self._save_persisted_state({"index": (index + 1) % len(RELEASES)})

        return result
