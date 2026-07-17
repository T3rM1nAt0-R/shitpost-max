#!/usr/bin/env python3
"""Cron entry point for the knuth-morris-pratt plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from knuth_morris_pratt_plugin import KnuthMorrisPrattPlugin  # noqa: E402


if __name__ == "__main__":
    KnuthMorrisPrattPlugin().run_tick()
