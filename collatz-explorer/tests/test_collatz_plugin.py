import json
import os
import sys
from pathlib import Path
import tempfile

import pytest

# Tests live in collatz-explorer/tests/; the module under test lives in
# collatz-explorer/, which imports `CollatzExplorerPlugin` from there.
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from collatz_plugin import CollatzExplorerPlugin


KNOWN_COLLATZ_STOPPING_TIMES = [
    0,
    1,
    7,
    2,
    5,
    8,
    16,
    3,
    19,
    6,
    14,
    9,
    9,
    17,
    17,
    4,
    12,
    20,
    20,
    7
]


def _plugin_in(tmpdir: str):
    """Return a CollatzExplorerPlugin whose plugin directory is ``tmpdir``."""
    return CollatzExplorerPlugin()


@pytest.mark.parametrize("n, expected", zip(range(1, 21), KNOWN_COLLATZ_STOPPING_TIMES))
def test_collatz_stopping_time(n, expected):
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        assert plugin._collatz_stopping_time(n) == expected

