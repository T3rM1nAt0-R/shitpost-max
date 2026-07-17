#!/usr/bin/env python3
"""Cron entry point for the random-walk-2d plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from random_walk_2d_plugin import RandomWalk2DPlugin  # noqa: E402


if __name__ == "__main__":
    RandomWalk2DPlugin().run_tick()
