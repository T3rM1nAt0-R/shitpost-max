#!/usr/bin/env python3
"""Cron entry point for the test_splitter plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from test_splitter_plugin import TestSplitterPlugin  # noqa: E402


if __name__ == "__main__":
    TestSplitterPlugin().run_tick()
