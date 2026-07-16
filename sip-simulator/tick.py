#!/usr/bin/env python3
"""Cron entry point for the sip_simulator plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from sip_simulator_plugin import SipSimulatorPlugin  # noqa: E402


if __name__ == "__main__":
    SipSimulatorPlugin().run_tick()
