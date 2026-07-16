#!/usr/bin/env python3
"""Cron entry point for the epidemic-sim plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from epidemic_sim_plugin import EpidemicSimPlugin  # noqa: E402


if __name__ == "__main__":
    EpidemicSimPlugin().run_tick()
