#!/usr/bin/env python3
"""Cron entry point for the stock_index_ticker plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from stock_index_ticker_plugin import StockIndexTickerPlugin  # noqa: E402


if __name__ == "__main__":
    StockIndexTickerPlugin().run_tick()
