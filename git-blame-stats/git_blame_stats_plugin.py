"""Reports a fixed embedded list of author/line-count blame stats, sorted by line count descending, cycling."""

from harness.shitpost_base import Shitpost

STATS = [
    ("alice", 4210),
    ("bob", 3150),
    ("carol", 1800),
    ("dave", 620),
]
SORTED = sorted(STATS, key=lambda s: -s[1])


class GitBlameStatsPlugin(Shitpost):
    """Emit one SORTED entry per tick, cycling through the list."""

    name = "git-blame-stats"
    internal = False
    commit_template = "blame-stats {author}: {line_count} lines"

    def produce(self) -> dict:
        state = self._load_persisted_state({"index": 0})
        index = state["index"]

        author, lines = SORTED[index]

        result = {
            "author": author,
            "line_count": lines,
        }

        self._save_persisted_state({"index": (index + 1) % len(SORTED)})

        return result
