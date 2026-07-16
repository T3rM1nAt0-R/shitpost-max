#!/usr/bin/env python3
"""Cron entry point for the lorem-ipsum-stream plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from lorem_ipsum_stream_plugin import LoremIpsumStreamPlugin  # noqa: E402


if __name__ == "__main__":
    LoremIpsumStreamPlugin().run_tick()
