#!/usr/bin/env python3
"""Cron entry point for the monty-hall-sim plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from monty_hall_sim_plugin import MontyHallSimPlugin  # noqa: E402


if __name__ == "__main__":
    MontyHallSimPlugin().run_tick()
