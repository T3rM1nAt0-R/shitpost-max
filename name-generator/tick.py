#!/usr/bin/env python3
"""Cron entry point for the name-generator plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from name_gen_plugin import NameGeneratorPlugin  # noqa: E402


if __name__ == "__main__":
    NameGeneratorPlugin().run_tick()
