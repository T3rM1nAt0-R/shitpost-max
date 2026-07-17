#!/usr/bin/env python3
"""Cron entry point for the aliquot_sequences plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from aliquot_sequences_plugin import AliquotSequencesPlugin  # noqa: E402


if __name__ == "__main__":
    AliquotSequencesPlugin().run_tick()
