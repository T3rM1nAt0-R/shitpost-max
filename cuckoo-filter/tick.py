#!/usr/bin/env python3
"""Cron entry point for the cuckoo_filter plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from cuckoo_filter_plugin import CuckooFilterPlugin  # noqa: E402


if __name__ == "__main__":
    CuckooFilterPlugin().run_tick()
