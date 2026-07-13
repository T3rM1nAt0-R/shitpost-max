#!/usr/bin/env python3
"""Cron entry point for the regex-of-the-day plugin."""

import os
import sys

# Make the repo root importable so ``harness.shitpost_base`` is available.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from regex_of_the_day_plugin import RegexOfTheDayPlugin  # noqa: E402


if __name__ == "__main__":
    RegexOfTheDayPlugin().run_tick()
