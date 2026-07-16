#!/usr/bin/env python3
"""Cron entry point for the bitcoin_fees plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from bitcoin_fees_plugin import BitcoinFeesPlugin  # noqa: E402


if __name__ == "__main__":
    BitcoinFeesPlugin().run_tick()
