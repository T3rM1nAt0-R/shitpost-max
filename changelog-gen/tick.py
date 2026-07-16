#!/usr/bin/env python3
"""Cron entry point for the changelog_gen plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from changelog_gen_plugin import ChangelogGenPlugin  # noqa: E402


if __name__ == "__main__":
    ChangelogGenPlugin().run_tick()
