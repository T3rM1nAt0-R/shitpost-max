#!/usr/bin/env python3
"""Cron entry point for the prompt-injection-lab plugin."""

import os
import sys

# Make the repo root importable so ``harness.shitpost_base`` is available.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from prompt_injection_lab_plugin import PromptInjectionLab  # noqa: E402


if __name__ == "__main__":
    PromptInjectionLab().run_tick()
