#!/usr/bin/env python3
"""Cron entry point for the commit-driven-development plugin."""

import os
import sys

# Make the repo root importable so ``harness.shitpost_base`` is available.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from commit_driven_development_plugin import CommitDrivenDevelopmentPlugin  # noqa: E402


if __name__ == "__main__":
    CommitDrivenDevelopmentPlugin().run_tick()
