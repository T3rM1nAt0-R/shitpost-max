#!/usr/bin/env python3
"""Cron entry point for the lumpsum_calculator plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from lumpsum_calculator_plugin import LumpsumCalculatorPlugin  # noqa: E402


if __name__ == "__main__":
    LumpsumCalculatorPlugin().run_tick()
