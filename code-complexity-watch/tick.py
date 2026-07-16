#!/usr/bin/env python3
"""Cron entry point for the code_complexity_watch plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from code_complexity_watch_plugin import CodeComplexityWatchPlugin  # noqa: E402


if __name__ == "__main__":
    CodeComplexityWatchPlugin().run_tick()
