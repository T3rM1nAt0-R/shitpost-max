"""Fetches the top N PyPI packages by 30-day download count each tick, cycling through the top 5."""

import json
import urllib.request

from harness.shitpost_base import Shitpost

ENDPOINT = "https://hugovk.github.io/top-pypi-packages/top-pypi-packages-30-days.json"
TOP_N = 5


def _parse(data):
    rows = data["rows"]
    if len(rows) < TOP_N:
        raise ValueError(f"expected at least {TOP_N} rows, found {len(rows)}")
    return [(r["project"], int(r["download_count"])) for r in rows[:TOP_N]]


class TopPypiPackagesPlugin(Shitpost):
    """Fetch the current top 5 PyPI packages and emit one per tick, cycling through them."""

    name = "top-pypi-packages"
    internal = False
    commit_template = "pypi #{rank} {project}: {download_count} downloads/30d"

    def produce(self):
        try:
            with urllib.request.urlopen(ENDPOINT, timeout=15) as response:
                data = json.loads(response.read())
            top5 = _parse(data)
        except Exception:
            return None

        state = self._load_persisted_state({"index": 0})
        index = state["index"]
        project, download_count = top5[index]

        result = {
            "rank": index + 1,
            "project": project,
            "download_count": download_count,
        }

        self._save_persisted_state({"index": (index + 1) % TOP_N})

        return result
