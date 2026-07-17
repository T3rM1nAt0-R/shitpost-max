import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from cuckoo_filter_plugin import (
    _fingerprint, _index1, _index2, _insert, _contains, _delete, _empty_buckets,
    CuckooFilterPlugin, OPERATIONS,
)

EXPECTED = [
    ("insert", "apple", True),
    ("insert", "banana", True),
    ("insert", "cherry", True),
    ("insert", "date", True),
    ("insert", "elderberry", True),
    ("lookup", "apple", True),
    ("lookup", "fig", False),
    ("delete", "banana", True),
    ("lookup", "banana", False),
]


def test_fixed_indices_and_fingerprints():
    assert _fingerprint("apple") == 31
    assert _index1("apple") == 0
    assert _index2(0, 31) == 3
    assert _fingerprint("banana") == 114
    assert _index1("banana") == 2
    assert _index2(2, 114) == 0


def test_operation_sequence_matches_ground_truth():
    buckets = _empty_buckets()
    for operation, item, expected_result in EXPECTED:
        if operation == "insert":
            result = _insert(buckets, item)
        elif operation == "lookup":
            result = _contains(buckets, item)
        else:
            result = _delete(buckets, item)
        assert result == expected_result
    fill_count = sum(1 for bucket in buckets for slot in bucket if slot != 0)
    assert fill_count == 4


def test_full_cycle_and_reset(tmp_path, monkeypatch):
    plugin = CuckooFilterPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    result = None
    for expected_op, expected_item, expected_result in EXPECTED:
        result = plugin.produce()
        assert result["operation"] == expected_op
        assert result["item"] == expected_item
        assert result["result"] == expected_result

    assert result["fill_count"] == 4

    next_result = plugin.produce()
    assert next_result["op_index"] == 0
    assert next_result["operation"] == OPERATIONS[0][0]
    assert next_result["fill_count"] == 1
