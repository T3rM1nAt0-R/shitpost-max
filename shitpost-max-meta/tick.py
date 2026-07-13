#!/usr/bin/env python3
"""Cron entry point for the shitpost-max-meta plugin."""

import os
import sys

# Make the repo root importable so ``harness.shitpost_base`` is available.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from shitpost_max_meta_plugin import MetaPlugin  # noqa: E402


if __name__ == "__main__":
    MetaPlugin().run_tick()
