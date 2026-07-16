#!/usr/bin/env python3
"""Cron entry point for the iterated-prisoner plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from iterated_prisoner_plugin import IteratedPrisonerPlugin  # noqa: E402


if __name__ == "__main__":
    IteratedPrisonerPlugin().run_tick()
