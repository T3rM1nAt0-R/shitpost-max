#!/usr/bin/env python3
"""Cron entry point for the emi_calculator plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from emi_calculator_plugin import EmiCalculatorPlugin  # noqa: E402


if __name__ == "__main__":
    EmiCalculatorPlugin().run_tick()
