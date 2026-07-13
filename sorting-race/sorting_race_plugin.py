import json
import os
import random
import sys
from datetime import datetime, timezone
import time

from harness.shitpost_base import Shitpost


class SortingRacePlugin(Shitpost):
    """Sort a list of 200 random integers using different algorithms."""

    name = "sorting-race"
    internal = False
    commit_template = "sorting-race: {algorithm} sorted {list_size} items in {elapsed_ms}ms"

    def __init__(self):
        super().__init__()
        self._state_file_name = "sorting_race_state.json"
        self._ALGORITHMS = [
            ("bubble_sort", bubble_sort),
            ("insertion_sort", insertion_sort),
            ("selection_sort", selection_sort),
            ("merge_sort", merge_sort)
        ]

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it at algo_index=0 and tick=0."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: sorting-race state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"algo_index", "tick"}
            if not required.issubset(state.keys()):
                print(
                    "warning: sorting-race state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "algo_index": 0,
            "tick": 0
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def produce(self) -> dict:
        """Return the next sorted list and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Generate a list of 200 random integers
        the_list = [random.randint(0, 10000) for _ in range(200)]

        # Get the current algorithm and advance to the next one
        name, func = self._ALGORITHMS[state["algo_index"] % len(self._ALGORITHMS)]
        state["algo_index"] += 1

        # Time the sorting function
        start = time.perf_counter()
        result = func(the_list)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Verify correctness
        assert result == sorted(the_list), "Sorting function is incorrect"

        # Advance tick
        state["tick"] += 1

        self._save_state(plugin_dir, state)

        return {
            "tick": state["tick"],
            "algorithm": name,
            "elapsed_ms": elapsed_ms,
            "list_size": 200,
            "sorted_prefix": result[:5],
            "sorted_suffix": result[-5:]
        }


def bubble_sort(lst):
    lst = list(lst)
    n = len(lst)
    for i in range(n):
        for j in range(0, n-i-1):
            if lst[j] > lst[j+1]:
                lst[j], lst[j+1] = lst[j+1], lst[j]
    return lst


def insertion_sort(lst):
    lst = list(lst)
    for i in range(1, len(lst)):
        key = lst[i]
        j = i - 1
        while j >= 0 and key < lst[j]:
            lst[j + 1] = lst[j]
            j -= 1
        lst[j + 1] = key
    return lst


def selection_sort(lst):
    lst = list(lst)
    for i in range(len(lst)):
        min_idx = i
        for j in range(i+1, len(lst)):
            if lst[min_idx] > lst[j]:
                min_idx = j
        lst[i], lst[min_idx] = lst[min_idx], lst[i]
    return lst


def merge_sort(lst):
    if len(lst) <= 1:
        return lst

    mid = len(lst) // 2
    left_half = merge_sort(lst[:mid])
    right_half = merge_sort(lst[mid:])

    return merge(left_half, right_half)


def merge(left, right):
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i] < right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])

    return result
