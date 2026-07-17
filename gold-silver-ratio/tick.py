#!/usr/bin/env python3
"""Cron entry point for the gold_silver_ratio plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from gold_silver_ratio_plugin import GoldSilverRatioPlugin  # noqa: E402


if __name__ == "__main__":
    GoldSilverRatioPlugin().run_tick()
