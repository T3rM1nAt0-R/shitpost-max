#!/usr/bin/env python3
"""Cron entry point for the dependency_watch plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from dependency_watch_plugin import DependencyWatchPlugin  # noqa: E402


if __name__ == "__main__":
    DependencyWatchPlugin().run_tick()
