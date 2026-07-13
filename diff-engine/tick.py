#!/usr/bin/env python3

import os
import sys

# Make the repo root importable so ``harness.shitpost_base`` is available.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from diff_engine_plugin import DiffEnginePlugin  # noqa: E402


if __name__ == "__main__":
    DiffEnginePlugin().run_tick()
