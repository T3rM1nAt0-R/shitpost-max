#!/usr/bin/env python3
"""Cron entry point for the covid_wastewater plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from covid_wastewater_plugin import CovidWastewaterPlugin  # noqa: E402


if __name__ == "__main__":
    CovidWastewaterPlugin().run_tick()
