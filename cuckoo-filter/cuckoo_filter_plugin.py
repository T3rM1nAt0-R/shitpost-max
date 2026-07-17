"""Maintains a small deterministic Cuckoo filter and runs a fixed insert/lookup/delete operation sequence."""

import hashlib

from harness.shitpost_base import Shitpost

NUM_BUCKETS = 8
BUCKET_SIZE = 4
MAX_KICKS = 20

OPERATIONS = [
    ("insert", "apple"),
    ("insert", "banana"),
    ("insert", "cherry"),
    ("insert", "date"),
    ("insert", "elderberry"),
    ("lookup", "apple"),
    ("lookup", "fig"),
    ("delete", "banana"),
    ("lookup", "banana"),
]


def _fingerprint(item):
    fp = int(hashlib.md5(item.encode()).hexdigest()[:2], 16)
    return fp if fp != 0 else 1


def _index1(item):
    return int(hashlib.md5(item.encode()).hexdigest()[2:6], 16) % NUM_BUCKETS


def _index2(idx1, fp):
    return (idx1 ^ (fp * 0x5bd1e995)) % NUM_BUCKETS


def _insert(buckets, item):
    fp = _fingerprint(item)
    i1 = _index1(item)
    i2 = _index2(i1, fp)
    for idx in (i1, i2):
        if 0 in buckets[idx]:
            buckets[idx][buckets[idx].index(0)] = fp
            return True
    idx = i1
    cur_fp = fp
    for _ in range(MAX_KICKS):
        evicted = buckets[idx][0]
        buckets[idx][0] = cur_fp
        cur_fp = evicted
        idx = _index2(idx, cur_fp)
        if 0 in buckets[idx]:
            buckets[idx][buckets[idx].index(0)] = cur_fp
            return True
    return False


def _contains(buckets, item):
    fp = _fingerprint(item)
    i1 = _index1(item)
    i2 = _index2(i1, fp)
    return fp in buckets[i1] or fp in buckets[i2]


def _delete(buckets, item):
    fp = _fingerprint(item)
    i1 = _index1(item)
    i2 = _index2(i1, fp)
    for idx in (i1, i2):
        if fp in buckets[idx]:
            buckets[idx][buckets[idx].index(fp)] = 0
            return True
    return False


def _empty_buckets():
    return [[0] * BUCKET_SIZE for _ in range(NUM_BUCKETS)]


class CuckooFilterPlugin(Shitpost):
    """Apply one fixed OPERATIONS entry per tick to a persisted Cuckoo filter, resetting after the last one."""

    name = "cuckoo-filter"
    internal = False
    commit_template = "cuckoo {operation}({item}): {result}"

    def produce(self):
        state = self._load_persisted_state({"op_index": 0, "buckets": _empty_buckets()})
        op_index = state["op_index"]
        buckets = state["buckets"]

        operation, item = OPERATIONS[op_index]
        if operation == "insert":
            result = _insert(buckets, item)
        elif operation == "lookup":
            result = _contains(buckets, item)
        else:
            result = _delete(buckets, item)

        fill_count = sum(1 for bucket in buckets for slot in bucket if slot != 0)

        response = {
            "op_index": op_index,
            "operation": operation,
            "item": item,
            "result": result,
            "fill_count": fill_count,
        }

        if op_index == len(OPERATIONS) - 1:
            self._save_persisted_state({"op_index": 0, "buckets": _empty_buckets()})
        else:
            self._save_persisted_state({"op_index": op_index + 1, "buckets": buckets})

        return response
