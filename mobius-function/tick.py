#!/usr/bin/env python3
"""Cron entry point for the mobius-function plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from mobius_function_plugin import MobiusFunctionPlugin  # noqa: E402


if __name__ == "__main__":
    MobiusFunctionPlugin().run_tick()
