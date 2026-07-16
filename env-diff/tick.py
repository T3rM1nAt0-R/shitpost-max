#!/usr/bin/env python3
"""Cron entry point for the env_diff plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from env_diff_plugin import EnvDiffPlugin  # noqa: E402


if __name__ == "__main__":
    EnvDiffPlugin().run_tick()
