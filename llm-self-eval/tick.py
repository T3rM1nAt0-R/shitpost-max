#!/usr/bin/env python3
"""Cron entry point for the llm_self_eval plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from llm_self_eval_plugin import LlmSelfEvalPlugin  # noqa: E402


if __name__ == "__main__":
    LlmSelfEvalPlugin().run_tick()
