#!/usr/bin/env python3
"""Cron entry point for the retirement_sim plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from retirement_sim_plugin import RetirementSimPlugin  # noqa: E402


if __name__ == "__main__":
    RetirementSimPlugin().run_tick()
