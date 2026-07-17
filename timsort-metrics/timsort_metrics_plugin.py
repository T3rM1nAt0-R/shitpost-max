"""Benchmarking the industry-standard hybrid sorting algorithm with AI-driven performance analytics. Comparison counts are the new revenue."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class TimsortMetricsPlugin(Shitpost):
    """Run a counting merge sort on a fixed cycling array, reporting comparison and merge counts."""

    name = "timsort-metrics"
    internal = False
    commit_template = "sort pass #{array_index}: {comparisons} comparisons, {merges} merges"

    _ARRAYS = [
        [5, 2, 8, 1, 9, 3],
        [4, 4, 4, 4],
        [1],
        [9, 8, 7, 6, 5, 4, 3, 2, 1],
    ]

    @classmethod
    def _counting_merge_sort(cls, arr: list) -> tuple:
        counters = {"comparisons": 0, "merges": 0}

        def merge_sort(a):
            if len(a) <= 1:
                return a
            mid = len(a) // 2
            left = merge_sort(a[:mid])
            right = merge_sort(a[mid:])
            counters["merges"] += 1
            return merge(left, right)

        def merge(left, right):
            result = []
            i = j = 0
            while i < len(left) and j < len(right):
                counters["comparisons"] += 1
                if left[i] <= right[j]:
                    result.append(left[i])
                    i += 1
                else:
                    result.append(right[j])
                    j += 1
            result.extend(left[i:])
            result.extend(right[j:])
            return result

        sorted_arr = merge_sort(list(arr))
        return sorted_arr, counters["comparisons"], counters["merges"]

    def produce(self) -> dict:
        """Run the counting merge sort on the current array and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "array_index": 0,
            "tick": 0,
        })

        array_index = state["array_index"]
        arr = self._ARRAYS[array_index % len(self._ARRAYS)]
        _, comparisons, merges = self._counting_merge_sort(arr)

        state["array_index"] += 1
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "array_index": array_index,
            "comparisons": comparisons,
            "merges": merges,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
