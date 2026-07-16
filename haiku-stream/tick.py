#!/usr/bin/env python3
"""Cron entry point for the haiku-stream plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from haiku_stream_plugin import HaikuStreamPlugin  # noqa: E402


if __name__ == "__main__":
    HaikuStreamPlugin().run_tick()
