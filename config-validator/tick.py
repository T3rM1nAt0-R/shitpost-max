#!/usr/bin/env python3
"""Cron entry point for the config_validator plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from config_validator_plugin import ConfigValidatorPlugin  # noqa: E402


if __name__ == "__main__":
    ConfigValidatorPlugin().run_tick()
