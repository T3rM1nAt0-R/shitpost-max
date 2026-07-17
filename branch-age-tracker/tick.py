#!/usr/bin/env python3
"""Cron entry point for the branch_age_tracker plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from branch_age_tracker_plugin import BranchAgeTrackerPlugin  # noqa: E402


if __name__ == "__main__":
    BranchAgeTrackerPlugin().run_tick()
