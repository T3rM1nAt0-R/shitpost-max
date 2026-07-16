#!/usr/bin/env python3
"""Cron entry point for the sieving-sundaram plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from sieving_sundaram_plugin import SievingSundaramPlugin  # noqa: E402


if __name__ == "__main__":
    SievingSundaramPlugin().run_tick()
