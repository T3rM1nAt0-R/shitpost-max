#!/usr/bin/env python3
"""Cron entry point for the regression-canary plugin."""

import os
import sys

# Make the repo root importable so ``harness.shitpost_base`` is available.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from regression_canary_plugin import RegressionCanaryPlugin


if __name__ == "__main__":
    plugin = RegressionCanaryPlugin()
    result = plugin.produce()
    print(result)
