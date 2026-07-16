#!/usr/bin/env python3
"""Cron entry point for the conway-life plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from conway_life_plugin import ConwayLifePlugin  # noqa: E402


if __name__ == "__main__":
    ConwayLifePlugin().run_tick()
