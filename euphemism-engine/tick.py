#!/usr/bin/env python3
"""Cron entry point for the euphemism-engine plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from euphemism_engine_plugin import EuphemismEnginePlugin  # noqa: E402


if __name__ == "__main__":
    EuphemismEnginePlugin().run_tick()
