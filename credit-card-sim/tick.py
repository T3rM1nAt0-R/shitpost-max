#!/usr/bin/env python3
"""Cron entry point for the credit_card_sim plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from credit_card_sim_plugin import CreditCardSimPlugin  # noqa: E402


if __name__ == "__main__":
    CreditCardSimPlugin().run_tick()
