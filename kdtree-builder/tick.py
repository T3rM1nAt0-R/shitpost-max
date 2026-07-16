#!/usr/bin/env python3
"""Cron entry point for the kdtree-builder plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from kdtree_builder_plugin import KdtreeBuilderPlugin  # noqa: E402


if __name__ == "__main__":
    KdtreeBuilderPlugin().run_tick()
