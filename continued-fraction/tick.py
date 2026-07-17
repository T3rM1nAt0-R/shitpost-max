#!/usr/bin/env python3
"""Cron entry point for the continued-fraction plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from continued_fraction_plugin import ContinuedFractionPlugin  # noqa: E402


if __name__ == "__main__":
    ContinuedFractionPlugin().run_tick()
