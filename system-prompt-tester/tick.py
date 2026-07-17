#!/usr/bin/env python3
"""Cron entry point for the system_prompt_tester plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from system_prompt_tester_plugin import SystemPromptTesterPlugin  # noqa: E402


if __name__ == "__main__":
    SystemPromptTesterPlugin().run_tick()
