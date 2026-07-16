#!/usr/bin/env python3
"""Cron entry point for the levenshtein-watch plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from levenshtein_watch_plugin import LevenshteinWatchPlugin  # noqa: E402


if __name__ == "__main__":
    LevenshteinWatchPlugin().run_tick()
