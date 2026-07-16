#!/usr/bin/env python3
"""Cron entry point for the multiplicative-persistence plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from multiplicative_persistence_plugin import MultiplicativePersistencePlugin  # noqa: E402


if __name__ == "__main__":
    MultiplicativePersistencePlugin().run_tick()
