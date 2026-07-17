#!/usr/bin/env python3
"""Cron entry point for the look_and_say plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from look_and_say_plugin import LookAndSayPlugin  # noqa: E402


if __name__ == "__main__":
    LookAndSayPlugin().run_tick()
