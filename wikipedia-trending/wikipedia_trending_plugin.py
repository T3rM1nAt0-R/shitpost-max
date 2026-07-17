"""Fetches yesterday's top viewed English Wikipedia articles daily, filtering out navigation/meta pages -- because "Main_Page" being #1 forever isn't trending, it's just the URL bar."""

import json
import urllib.request
from datetime import datetime, timedelta, timezone

from harness.shitpost_base import Shitpost

ENDPOINT_TEMPLATE = (
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/top/"
    "en.wikipedia/all-access/{year}/{month:02d}/{day:02d}"
)
EXCLUDE_PREFIXES = ("Special:", "Wikipedia:", "Portal:", "File:", "Talk:", "Help:", "Category:", "Template:")
EXCLUDE_EXACT = {"Main_Page"}
TOP_N = 5


def _parse(data):
    articles = data["items"][0]["articles"]
    filtered = [
        a for a in articles
        if a["article"] not in EXCLUDE_EXACT and not a["article"].startswith(EXCLUDE_PREFIXES)
    ]
    if len(filtered) < TOP_N:
        raise ValueError(f"expected at least {TOP_N} articles after filtering, found {len(filtered)}")
    return [(a["article"], a["views"]) for a in filtered[:TOP_N]]


class WikipediaTrendingPlugin(Shitpost):
    """Fetch yesterday's top 5 (filtered) Wikipedia articles and emit one per tick, cycling."""

    name = "wikipedia-trending"
    internal = False
    commit_template = "wikipedia-trending #{rank} {article}: {views} views"

    def produce(self):
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        url = ENDPOINT_TEMPLATE.format(year=yesterday.year, month=yesterday.month, day=yesterday.day)

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "shitpost-max/wikipedia-trending"})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read())
            top5 = _parse(data)
        except Exception:
            return None

        state = self._load_persisted_state({"index": 0})
        index = state["index"]
        article, views = top5[index]

        result = {
            "rank": index + 1,
            "article": article,
            "views": views,
            "date": yesterday.strftime("%Y-%m-%d"),
        }

        self._save_persisted_state({"index": (index + 1) % TOP_N})

        return result
