#!/usr/bin/env python3
"""Cron entry point for the economy-sim-tick plugin."""

import os
import sys

# Make the repo root importable so ``harness.shitpost_base`` is available.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from economy_sim_tick_plugin import EconomySimTickPlugin  # noqa: E402


if __name__ == "__main__":
    EconomySimTickPlugin().run_tick()
