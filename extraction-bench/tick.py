#!/usr/bin/env python3
"""Cron entry point for the extraction_bench plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from extraction_bench_plugin import ExtractionBenchPlugin  # noqa: E402


if __name__ == "__main__":
    ExtractionBenchPlugin().run_tick()
