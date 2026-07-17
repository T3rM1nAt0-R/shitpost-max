#!/usr/bin/env python3
"""Cron entry point for the regression-canary plugin."""

import os
import sys

# Make the repo root importable so ``harness.shitpost_base`` is available.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from regression_canary_plugin import RegressionCanaryPlugin


if __name__ == "__main__":
    # Real bug, found 2026-07-17: this called produce() directly and printed
    # the result, never .run_tick() -- so the harness's persistence
    # (_append_state/_write_summary) and git commit never happened,
    # regardless of what produce() returned. Every other plugin's tick.py
    # calls .run_tick(); this one never did.
    RegressionCanaryPlugin().run_tick()
