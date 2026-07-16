#!/usr/bin/env python3
"""Cron entry point for the multi-armed-bandit plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from multi_armed_bandit_plugin import MultiArmedBanditPlugin  # noqa: E402


if __name__ == "__main__":
    MultiArmedBanditPlugin().run_tick()
