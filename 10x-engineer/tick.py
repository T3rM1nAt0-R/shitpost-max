#!/usr/bin/env python3
"""Cron entry point for the 10x-engineer plugin."""

import importlib.util
import os
import sys

# Make the repo root importable so ``harness.shitpost_base`` is available.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)

# "10x_engineer_plugin" isn't a valid Python identifier (starts with a
# digit), so a literal `from 10x_engineer_plugin import ...` is a syntax
# error, not just a missing-module error -- load it by file path instead.
_MODULE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "10x_engineer_plugin.py")
_spec = importlib.util.spec_from_file_location("tenx_engineer_plugin", _MODULE_PATH)
_mod = importlib.util.module_from_spec(_spec)
# _plugin_dir() (harness/shitpost_base.py) looks itself up via
# sys.modules[self.__class__.__module__] -- must be registered there
# under the same name passed to spec_from_file_location, or that lookup
# KeyErrors.
sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)
TenXEngineerPlugin = _mod.TenXEngineerPlugin


if __name__ == "__main__":
    TenXEngineerPlugin().run_tick()
