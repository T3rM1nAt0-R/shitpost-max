#!/usr/bin/env python3
"""Cron entry point for the radix-sort-tick plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from radix_sort_tick_plugin import RadixSortTickPlugin  # noqa: E402


if __name__ == "__main__":
    RadixSortTickPlugin().run_tick()
