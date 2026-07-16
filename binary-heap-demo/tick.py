#!/usr/bin/env python3
"""Cron entry point for the binary-heap-demo plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from binary_heap_demo_plugin import BinaryHeapDemoPlugin  # noqa: E402


if __name__ == "__main__":
    BinaryHeapDemoPlugin().run_tick()
