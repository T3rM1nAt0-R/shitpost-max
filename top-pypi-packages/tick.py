#!/usr/bin/env python3
"""Cron entry point for the top_pypi_packages plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from top_pypi_packages_plugin import TopPypiPackagesPlugin  # noqa: E402


if __name__ == "__main__":
    TopPypiPackagesPlugin().run_tick()
