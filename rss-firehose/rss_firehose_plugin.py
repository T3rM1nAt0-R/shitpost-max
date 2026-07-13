import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List

import feedparser
import requests

from harness.shitpost_base import Shitpost


class RSSFirehosePlugin(Shitpost):
    """Poll ~20 RSS feeds and commit only new items, deduplicated, logged to JSONL."""

    name = "rss-firehose"
    internal = False
    commit_template = "rss-firehose: {new_items} new from {feeds_checked} feeds"

    def __init__(self):
        super().__init__()
        self._state_file_name = "state.jsonl"
        self._seen_file_name = "seen.json"
        self._summary_file_name = "summary.json"
        self._feeds_file_name = "feeds.txt"

    def _load_state(self, plugin_dir: str) -> List[Dict]:
        """Load the running state, or initialise it as empty."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return [json.loads(line) for line in f]
            except json.JSONDecodeError as exc:
                print(
                    f"warning: state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
        return []

    def _save_state(self, plugin_dir: str, state: List[Dict]) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            for item in state:
                json.dump(item, f)
                f.write("\n")
        os.replace(tmp_path, path)

    def _load_seen(self, plugin_dir: str) -> set:
        """Load the set of seen items."""
        path = os.path.join(plugin_dir, self._seen_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return {line.strip() for line in f}
            except Exception as exc:
                print(
                    f"warning: seen file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
        return set()

    def _save_seen(self, plugin_dir: str, seen: set) -> None:
        path = os.path.join(plugin_dir, self._seen_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            for item in seen:
                f.write(item + "\n")
        os.replace(tmp_path, path)

    def _load_summary(self, plugin_dir: str) -> Dict:
        """Load the summary."""
        path = os.path.join(plugin_dir, self._summary_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: summary file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
        return {"new_items": 0, "feeds_checked": 0}

    def _save_summary(self, plugin_dir: str, summary: Dict) -> None:
        path = os.path.join(plugin_dir, self._summary_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _fetch_feeds(self) -> List[Dict]:
        """Fetch and parse feeds."""
        with open(os.path.join(self._plugin_dir(), self._feeds_file_name), "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]
        results = []
        for url in urls:
            try:
                response = requests.get(url, headers={"User-Agent": "rss-firehose"})
                response.raise_for_status()
                feed = feedparser.parse(response.content)
                results.extend(feed.entries)
            except Exception as exc:
                print(f"warning: failed to fetch {url} ({exc})", file=sys.stderr)
        return results

    def produce(self) -> dict:
        """Return the new items and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        seen = self._load_seen(plugin_dir)
        summary = self._load_summary(plugin_dir)

        new_items = []
        for item in self._fetch_feeds():
            guid = getattr(item, "guid", None) or item.link
            if guid not in seen:
                state.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "feed": item.feed.title,
                    "title": item.title,
                    "link": item.link,
                    "guid": guid,
                    "published": getattr(item, "published", None),
                })
                new_items.append(guid)
                seen.add(guid)

        summary["new_items"] += len(new_items)
        summary["feeds_checked"] += len(urls)

        self._save_state(plugin_dir, state)
        self._save_seen(plugin_dir, seen)
        self._save_summary(plugin_dir, summary)

        return {
            "tick": summary["feeds_checked"],
            "new_items": len(new_items),
            "feeds_checked": len(urls),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
