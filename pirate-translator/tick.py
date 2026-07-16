#!/usr/bin/env python3
"""Cron entry point for the pirate-translator plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from pirate_translator_plugin import PirateTranslatorPlugin  # noqa: E402


if __name__ == "__main__":
    PirateTranslatorPlugin().run_tick()
