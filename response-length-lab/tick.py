#!/usr/bin/env python3
"""Cron entry point for the response_length_lab plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from response_length_lab_plugin import ResponseLengthLabPlugin  # noqa: E402


if __name__ == "__main__":
    ResponseLengthLabPlugin().run_tick()
