#!/usr/bin/env python3
"""Cron entry point for the zero_shot_bench plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from zero_shot_bench_plugin import ZeroShotBenchPlugin  # noqa: E402


if __name__ == "__main__":
    ZeroShotBenchPlugin().run_tick()
