#!/usr/bin/env python3
"""Cron entry point for the aurora_forecast plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from aurora_forecast_plugin import AuroraForecastPlugin  # noqa: E402


if __name__ == "__main__":
    AuroraForecastPlugin().run_tick()
