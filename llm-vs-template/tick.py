#!/usr/bin/env python3
"""Cron entry point for the llm_vs_template plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from llm_vs_template_plugin import LlmVsTemplatePlugin  # noqa: E402


if __name__ == "__main__":
    LlmVsTemplatePlugin().run_tick()
