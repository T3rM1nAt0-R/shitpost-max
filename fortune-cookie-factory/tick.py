#!/usr/bin/env python3
"""Cron entry point for the fortune-cookie-factory plugin."""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

from fortune_cookie_factory_plugin import FortuneCookieFactoryPlugin  # noqa: E402


if __name__ == "__main__":
    FortuneCookieFactoryPlugin().run_tick()
