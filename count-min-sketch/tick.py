#!/usr/bin/env python3
"""Cron entry point for the count-min-sketch plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from count_min_sketch_plugin import CountMinSketchPlugin  # noqa: E402


if __name__ == "__main__":
    CountMinSketchPlugin().run_tick()
