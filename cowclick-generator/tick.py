#!/usr/bin/env python3
"""Cron entry point for the cowclick-generator plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from cowclick_generator_plugin import CowclickGeneratorPlugin  # noqa: E402


if __name__ == "__main__":
    CowclickGeneratorPlugin().run_tick()
