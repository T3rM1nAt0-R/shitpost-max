#!/usr/bin/env python3
"""Cron entry point for the token_counter_demo plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from token_counter_demo_plugin import TokenCounterDemoPlugin  # noqa: E402


if __name__ == "__main__":
    TokenCounterDemoPlugin().run_tick()
