#!/usr/bin/env python3
"""Cron entry point for the api_snapshot_diff plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from api_snapshot_diff_plugin import ApiSnapshotDiffPlugin  # noqa: E402


if __name__ == "__main__":
    ApiSnapshotDiffPlugin().run_tick()
