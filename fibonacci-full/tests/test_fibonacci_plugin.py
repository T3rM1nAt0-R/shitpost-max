import json
import os
import sys
import tempfile

import pytest

# Tests live in fibonacci-full/tests/; the module under test lives in
# fibonacci-full/, which in turn imports `harness.shitpost_base` from the repo
# root. Insert both so the tests are runnable regardless of cwd (previously
# only fibonacci-full/ was added, which worked only by accident when pytest's
# cwd-on-sys.path happened to already include the repo root - same class of
# bug found in golden-ratio's DeepSeek review, 2026-07-10).
_PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

import fibonacci_plugin  # noqa: E402


# First 20 Fibonacci numbers, F(0) through F(19).
KNOWN_FIB_20 = [
    0,
    1,
    1,
    2,
    3,
    5,
    8,
    13,
    21,
    34,
    55,
    89,
    144,
    233,
    377,
    610,
    987,
    1597,
    2584,
    4181,
]


def _plugin_in(tmpdir: str):
    """Return a FibonacciPlugin whose plugin directory is ``tmpdir``."""
    plugin = fibonacci_plugin.FibonacciPlugin()
    plugin._plugin_dir = lambda: tmpdir
    return plugin


def test_plugin_metadata():
    assert fibonacci_plugin.FibonacciPlugin.name == "fibonacci-full"
    assert fibonacci_plugin.FibonacciPlugin.internal is False
    assert (
        fibonacci_plugin.FibonacciPlugin.commit_template
        == "fibonacci F({n}): {fibonacci}"
    )


def test_first_twenty_numbers_are_correct():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        numbers = [plugin.produce()["fibonacci"] for _ in range(20)]
        assert numbers == KNOWN_FIB_20


def test_state_persists_across_plugin_instances():
    with tempfile.TemporaryDirectory() as tmp:
        first = _plugin_in(tmp)
        produced = [first.produce()["fibonacci"] for _ in range(10)]

        second = _plugin_in(tmp)
        more = [second.produce()["fibonacci"] for _ in range(10)]

        assert produced == KNOWN_FIB_20[:10]
        assert more == KNOWN_FIB_20[10:20]


def test_commit_template_formats_correctly():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        result = plugin.produce()
        message = plugin.commit_template.format(**result)
        assert message == f"fibonacci F({result['n']}): {result['fibonacci']}"


def test_fibonacci_txt_is_appended():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        for _ in range(12):
            plugin.produce()

        with open(os.path.join(tmp, "fibonacci.txt"), encoding="utf-8") as f:
            lines = f.read().splitlines()
        assert lines == [str(n) for n in KNOWN_FIB_20[:12]]


def test_fibonacci_state_file_contains_running_state():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        plugin.produce()

        state_path = os.path.join(tmp, "fibonacci_state.json")
        assert os.path.exists(state_path)
        with open(state_path, encoding="utf-8") as f:
            state = json.load(f)

        for key in ("a", "b", "n", "tick"):
            assert key in state
            assert isinstance(state[key], int)
        assert state["tick"] == 1
        assert state["n"] == 1


def test_produce_returns_required_fields():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        result = plugin.produce()
        assert result["fibonacci"] == 0
        assert result["tick"] == 1
        assert result["n"] == 0
        assert "timestamp" in result


def test_atomic_save_does_not_leave_stale_temp_file():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        plugin.produce()

        assert not os.path.exists(os.path.join(tmp, "fibonacci_state.json.tmp"))
        with open(os.path.join(tmp, "fibonacci_state.json"), encoding="utf-8") as f:
            state = json.load(f)
        assert state["tick"] == 1


def test_stale_temp_file_is_replaced_by_atomic_save():
    with tempfile.TemporaryDirectory() as tmp:
        stale_path = os.path.join(tmp, "fibonacci_state.json.tmp")
        with open(stale_path, "w", encoding="utf-8") as f:
            f.write("this is leftover garbage from a crashed write")

        plugin = _plugin_in(tmp)
        plugin.produce()

        assert not os.path.exists(stale_path)
        with open(os.path.join(tmp, "fibonacci_state.json"), encoding="utf-8") as f:
            state = json.load(f)
        assert state["tick"] == 1


def test_corrupt_state_file_self_heals(capsys):
    with tempfile.TemporaryDirectory() as tmp:
        state_path = os.path.join(tmp, "fibonacci_state.json")
        with open(state_path, "w", encoding="utf-8") as f:
            f.write("{not valid json")

        plugin = _plugin_in(tmp)
        result = plugin.produce()

        assert result["fibonacci"] == 0
        assert result["tick"] == 1
        assert result["n"] == 0
        with open(state_path, encoding="utf-8") as f:
            state = json.load(f)
        assert state["tick"] == 1
        captured = capsys.readouterr()
        assert "fibonacci state file is corrupt" in captured.err


def test_state_missing_keys_self_heals(capsys):
    with tempfile.TemporaryDirectory() as tmp:
        state_path = os.path.join(tmp, "fibonacci_state.json")
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump({"a": 0, "tick": 5}, f)

        plugin = _plugin_in(tmp)
        result = plugin.produce()

        assert result["fibonacci"] == 0
        assert result["tick"] == 1
        assert result["n"] == 0
        captured = capsys.readouterr()
        assert "fibonacci state missing keys" in captured.err
