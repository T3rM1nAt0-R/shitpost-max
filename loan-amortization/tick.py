#!/usr/bin/env python3
"""Cron entry point for the loan_amortization plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from loan_amortization_plugin import LoanAmortizationPlugin  # noqa: E402


if __name__ == "__main__":
    LoanAmortizationPlugin().run_tick()
