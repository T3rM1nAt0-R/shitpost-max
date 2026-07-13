import os
import sys
from pathlib import Path

import pytest

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from collatz_plugin import CollatzExplorerPlugin


KNOWN_COLLATZ_STOPPING_TIMES = [0, 1, 7, 2, 5, 8, 16, 3, 19, 6, 14, 9, 9, 17, 17, 4, 12, 20, 20, 7]
KNOWN_RECORDS = [(1, 0), (2, 1), (3, 7), (6, 8), (7, 16), (9, 19)]


@pytest.mark.parametrize("n, expected", zip(range(1, 21), KNOWN_COLLATZ_STOPPING_TIMES))
def test_collatz_stopping_time(n, expected):
    assert CollatzExplorerPlugin()._collatz_stopping_time(n) == expected


def test_produce_end_to_end_records_match_ground_truth(tmp_path, monkeypatch):
    plugin = CollatzExplorerPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    found_records = []
    for _ in range(9):
        result = plugin.produce()
        if result is not None:
            found_records.append((result["n"], result["steps"]))

    assert found_records == KNOWN_RECORDS

    records_txt = (tmp_path / "records.txt").read_text()
    assert records_txt.count("\n") == len(KNOWN_RECORDS)


def test_corrupt_state_file_handled(tmp_path, monkeypatch):
    plugin = CollatzExplorerPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    (tmp_path / "collatz_state.json").write_text("not valid json{{{")
    result = plugin.produce()
    assert result is not None  # n=1 (0 steps) is always a record on fresh state
