#!/usr/bin/env python3

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from bloom import BloomFilterDemo  # noqa: E402


if __name__ == "__main__":
    BloomFilterDemo().run_tick()
