#!/usr/bin/env python3
"""Cron entry point for the schelling-segregation plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from schelling_segregation_plugin import SchellingSegregationPlugin  # noqa: E402


if __name__ == "__main__":
    SchellingSegregationPlugin().run_tick()
