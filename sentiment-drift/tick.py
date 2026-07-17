#!/usr/bin/env python3
"""Cron entry point for the sentiment_drift plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from sentiment_drift_plugin import SentimentDriftPlugin  # noqa: E402


if __name__ == "__main__":
    SentimentDriftPlugin().run_tick()
