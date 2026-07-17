#!/usr/bin/env python3
"""Cron entry point for the timsort-metrics plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from timsort_metrics_plugin import TimsortMetricsPlugin  # noqa: E402


if __name__ == "__main__":
    TimsortMetricsPlugin().run_tick()
