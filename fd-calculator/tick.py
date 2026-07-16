#!/usr/bin/env python3
"""Cron entry point for the fd_calculator plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from fd_calculator_plugin import FdCalculatorPlugin  # noqa: E402


if __name__ == "__main__":
    FdCalculatorPlugin().run_tick()
