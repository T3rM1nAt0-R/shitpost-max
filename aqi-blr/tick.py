#!/usr/bin/env python3
"""Cron entry point for the aqi-blr plugin."""

import os
import sys

# Make the repo root importable so ``harness.shitpost_base`` is available.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from aqi_blr_plugin import AqiBlrPlugin  # noqa: E402


if __name__ == "__main__":
    AqiBlrPlugin().run_tick()
