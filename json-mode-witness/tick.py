#!/usr/bin/env python3
"""Cron entry point for the json-mode-witness plugin."""

import os
import sys

# Make the repo root importable so ``harness.shitpost_base`` is available.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from json_mode_witness_plugin import JsonModeWitnessPlugin  # noqa: E402


if __name__ == "__main__":
    JsonModeWitnessPlugin().run_tick()
