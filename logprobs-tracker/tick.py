#!/usr/bin/env python3
"""Cron entry point for the logprobs_tracker plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from logprobs_tracker_plugin import LogprobsTrackerPlugin  # noqa: E402


if __name__ == "__main__":
    LogprobsTrackerPlugin().run_tick()
