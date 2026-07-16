#!/usr/bin/env python3
"""Cron entry point for the portmanteau-gen plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from portmanteau_gen_plugin import PortmanteauGenPlugin  # noqa: E402


if __name__ == "__main__":
    PortmanteauGenPlugin().run_tick()
