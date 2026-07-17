#!/usr/bin/env python3
"""Cron entry point for the wikipedia-trending plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from wikipedia_trending_plugin import WikipediaTrendingPlugin  # noqa: E402


if __name__ == "__main__":
    WikipediaTrendingPlugin().run_tick()
