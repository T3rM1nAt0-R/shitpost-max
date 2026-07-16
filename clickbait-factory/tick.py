#!/usr/bin/env python3
"""Cron entry point for the clickbait-factory plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from clickbait_factory_plugin import ClickbaitFactoryPlugin  # noqa: E402


if __name__ == "__main__":
    ClickbaitFactoryPlugin().run_tick()
