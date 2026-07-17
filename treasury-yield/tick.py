#!/usr/bin/env python3
"""Cron entry point for the treasury_yield plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from treasury_yield_plugin import TreasuryYieldPlugin  # noqa: E402


if __name__ == "__main__":
    TreasuryYieldPlugin().run_tick()
