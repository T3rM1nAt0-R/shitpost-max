#!/usr/bin/env python3
"""Cron entry point for the moon_phase plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from moon_phase_plugin import MoonPhasePlugin  # noqa: E402


if __name__ == "__main__":
    MoonPhasePlugin().run_tick()
