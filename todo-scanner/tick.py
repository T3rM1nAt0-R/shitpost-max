#!/usr/bin/env python3
"""Cron entry point for the todo_scanner plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from todo_scanner_plugin import TodoScannerPlugin  # noqa: E402


if __name__ == "__main__":
    TodoScannerPlugin().run_tick()
