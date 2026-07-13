#!/usr/bin/env python3
"""Cron entry point for the reddit-titles plugin."""

import os
import sys

# Make the repo root importable so ``harness.shitpost_base`` is available.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from reddit_titles_plugin import RedditTitlesPlugin  # noqa: E402


if __name__ == "__main__":
    RedditTitlesPlugin().run_tick()
