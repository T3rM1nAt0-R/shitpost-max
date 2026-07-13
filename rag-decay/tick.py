#!/usr/bin/env python3
"""Cron entry point for the rag-decay plugin."""

import os
import sys

# Make the repo root importable so ``harness.shitpost_base`` is available.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from rag_decay_plugin import RagDecayPlugin


if __name__ == "__main__":
    plugin = RagDecayPlugin()
    result = plugin.produce()
    print(json.dumps(result, indent=2))
