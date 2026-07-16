#!/usr/bin/env python3
"""Cron entry point for the happy-numbers plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from happy_numbers_plugin import HappyNumbersPlugin  # noqa: E402


if __name__ == "__main__":
    HappyNumbersPlugin().run_tick()
