#!/usr/bin/env python3
"""Cron entry point for the minhash-sig plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from minhash_sig_plugin import MinhashSigPlugin  # noqa: E402


if __name__ == "__main__":
    MinhashSigPlugin().run_tick()
