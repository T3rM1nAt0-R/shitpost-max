#!/usr/bin/env python3
"""Cron entry point for the hyperloglog-estimator plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from hyperloglog_estimator_plugin import HyperloglogEstimatorPlugin  # noqa: E402


if __name__ == "__main__":
    HyperloglogEstimatorPlugin().run_tick()
