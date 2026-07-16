"""Fetches question counts for a fixed list of StackOverflow tags each tick, cycling through them."""

import json
import urllib.request

from harness.shitpost_base import Shitpost

TAGS = ["python", "javascript", "rust", "go", "typescript"]
ENDPOINT_TEMPLATE = "https://api.stackexchange.com/2.3/tags/{tag}/info?site=stackoverflow"


def _parse(data):
    items = data["items"]
    if not items:
        raise ValueError("empty items list")
    item = items[0]
    return {"tag": item["name"], "count": int(item["count"])}


class StackoverflowTagsPlugin(Shitpost):
    """Fetch and emit the question count for one fixed tag per tick, cycling through TAGS."""

    name = "stackoverflow-tags"
    internal = False
    commit_template = "so-tag {tag}: {count} questions"

    def produce(self):
        state = self._load_persisted_state({"index": 0})
        index = state["index"]
        tag = TAGS[index]

        try:
            url = ENDPOINT_TEMPLATE.format(tag=tag)
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read())
            result = _parse(data)
        except Exception:
            return None

        self._save_persisted_state({"index": (index + 1) % len(TAGS)})

        return result
