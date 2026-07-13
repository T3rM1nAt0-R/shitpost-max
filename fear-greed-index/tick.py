#!/usr/bin/env python3
"""Cron entry point for the fear-greed-index plugin."""

import os
import sys

# Make the repo root importable so ``harness.shitpost_base`` is available.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from fear_greed_index_plugin import FearGreedIndexPlugin  # noqa: E402


if __name__ == "__main__":
    FearGreedIndexPlugin().run_tick()
