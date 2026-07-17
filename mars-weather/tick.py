#!/usr/bin/env python3
"""Cron entry point for the mars_weather plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from mars_weather_plugin import MarsWeatherPlugin  # noqa: E402


if __name__ == "__main__":
    MarsWeatherPlugin().run_tick()
