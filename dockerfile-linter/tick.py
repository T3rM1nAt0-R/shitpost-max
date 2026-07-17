#!/usr/bin/env python3
"""Cron entry point for the dockerfile_linter plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from dockerfile_linter_plugin import DockerfileLinterPlugin  # noqa: E402


if __name__ == "__main__":
    DockerfileLinterPlugin().run_tick()
