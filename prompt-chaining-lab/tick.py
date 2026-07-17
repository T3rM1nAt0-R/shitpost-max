#!/usr/bin/env python3
"""Cron entry point for the prompt_chaining_lab plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from prompt_chaining_lab_plugin import PromptChainingLabPlugin  # noqa: E402


if __name__ == "__main__":
    PromptChainingLabPlugin().run_tick()
