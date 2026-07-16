#!/usr/bin/env python3
"""Cron entry point for the langton-ant plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from langton_ant_plugin import LangtonAntPlugin  # noqa: E402


if __name__ == "__main__":
    LangtonAntPlugin().run_tick()
