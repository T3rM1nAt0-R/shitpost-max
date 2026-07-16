#!/usr/bin/env python3
"""Cron entry point for the stern-brocot plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from stern_brocot_plugin import SternBrocotPlugin  # noqa: E402


if __name__ == "__main__":
    SternBrocotPlugin().run_tick()
