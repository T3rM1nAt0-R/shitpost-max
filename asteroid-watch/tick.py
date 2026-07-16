#!/usr/bin/env python3
"""Cron entry point for the asteroid_watch plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from asteroid_watch_plugin import AsteroidWatchPlugin  # noqa: E402


if __name__ == "__main__":
    AsteroidWatchPlugin().run_tick()
