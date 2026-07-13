#!/usr/bin/env python3
"""Cron entry point for the lru-cache-witness plugin."""
import os, sys
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lru_witness_plugin import LRUCacheWitnessPlugin  # noqa: E402
if __name__ == "__main__":
    LRUCacheWitnessPlugin().run_tick()
