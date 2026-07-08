import json
import os
import sys
import tempfile

import pytest

# Tests live in tests/; the module under test lives in base-converter/.
# The repo root is also needed so the shared ``harness`` package is importable.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, os.path.join(_REPO_ROOT, "base-converter"))

import converter  # noqa: E402


def _plugin_in(tmpdir: str):
    """Return a BaseConverterPlugin whose plugin directory is ``tmpdir``."""
    plugin = converter.BaseConverterPlugin()
    plugin._plugin_dir = lambda: tmpdir
    return plugin


def test_plugin_metadata():
    assert converter.BaseConverterPlugin.name == "base-converter"
    assert converter.BaseConverterPlugin.internal is False
    assert (
        converter.BaseConverterPlugin.commit_template
        == "base-converter: {value} in base {base} = {representation}"
    )


def test_counter_increments_and_persists_across_instances():
    with tempfile.TemporaryDirectory() as tmp:
        first = _plugin_in(tmp)
        first_results = [first.produce() for _ in range(5)]

        second = _plugin_in(tmp)
        second_results = [second.produce() for _ in range(5)]

        all_values = [r["value"] for r in first_results + second_results]
        assert all_values == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        counter_path = os.path.join(tmp, "counter.json")
        with open(counter_path, encoding="utf-8") as f:
            assert json.load(f) == {"value": 10}


def test_base_cycles_through_2_to_36():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        results = [plugin.produce() for _ in range(37)]

        bases = [r["base"] for r in results]
        assert bases[:35] == list(range(2, 37))
        assert bases[35] == 2
        assert bases[36] == 3


def test_tick_number_is_zero_indexed_call_count():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        results = [plugin.produce() for _ in range(5)]
        assert [r["tick_number"] for r in results] == [0, 1, 2, 3, 4]


@pytest.mark.parametrize(
    "value,base",
    [
        (0, 2),
        (1, 2),
        (42, 2),
        (255, 16),
        (4096, 16),
        (999_999, 36),
        (10_000, 10),
        (7, 8),
    ],
)
def test_to_base_round_trips(value, base):
    representation = converter.BaseConverterPlugin.to_base(value, base)
    assert int(representation, base) == value


def test_to_base_edge_cases():
    assert converter.BaseConverterPlugin.to_base(0, 2) == "0"
    assert converter.BaseConverterPlugin.to_base(0, 36) == "0"
    assert converter.BaseConverterPlugin.to_base(35, 36) == "z"
    assert converter.BaseConverterPlugin.to_base(36, 36) == "10"


def test_to_base_rejects_invalid_bases():
    with pytest.raises(ValueError, match="Base must be between 2 and 36"):
        converter.BaseConverterPlugin.to_base(1, 1)
    with pytest.raises(ValueError, match="Base must be between 2 and 36"):
        converter.BaseConverterPlugin.to_base(1, 37)


def test_to_base_rejects_negative_numbers():
    with pytest.raises(ValueError, match="Only non-negative integers are supported"):
        converter.BaseConverterPlugin.to_base(-1, 10)


def test_commit_template_formats_correctly():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        result = plugin.produce()
        message = plugin.commit_template.format(**result)
        expected = (
            f"base-converter: {result['value']} in base {result['base']} = "
            f"{result['representation']}"
        )
        assert message == expected


def test_counter_state_file_is_written():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        plugin.produce()

        counter_path = os.path.join(tmp, "counter.json")
        assert os.path.exists(counter_path)
        with open(counter_path, encoding="utf-8") as f:
            assert json.load(f) == {"value": 1}


def test_atomic_save_does_not_leave_temp_file():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        plugin.produce()

        assert not os.path.exists(os.path.join(tmp, "counter.json.tmp"))


def test_stale_temp_file_is_replaced_by_atomic_save():
    with tempfile.TemporaryDirectory() as tmp:
        stale_path = os.path.join(tmp, "counter.json.tmp")
        with open(stale_path, "w", encoding="utf-8") as f:
            f.write("leftover garbage")

        plugin = _plugin_in(tmp)
        plugin.produce()

        assert not os.path.exists(stale_path)
        with open(os.path.join(tmp, "counter.json"), encoding="utf-8") as f:
            assert json.load(f) == {"value": 1}


def test_corrupt_state_file_self_heals(capsys):
    with tempfile.TemporaryDirectory() as tmp:
        counter_path = os.path.join(tmp, "counter.json")
        with open(counter_path, "w", encoding="utf-8") as f:
            f.write("{not valid json")

        plugin = _plugin_in(tmp)
        result = plugin.produce()

        assert result["value"] == 1
        assert result["base"] == 2
        with open(counter_path, encoding="utf-8") as f:
            assert json.load(f) == {"value": 1}

        captured = capsys.readouterr()
        assert "counter state file is corrupt" in captured.err


@pytest.mark.parametrize("payload", ["5", "[1, 2, 3]", "\"hello\""])
def test_valid_non_dict_state_file_self_heals(payload, capsys):
    """Valid JSON that isn't a dict should self-heal to a fresh counter."""
    with tempfile.TemporaryDirectory() as tmp:
        counter_path = os.path.join(tmp, "counter.json")
        with open(counter_path, "w", encoding="utf-8") as f:
            f.write(payload)

        plugin = _plugin_in(tmp)
        result = plugin.produce()

        assert result["value"] == 1
        assert result["base"] == 2
        with open(counter_path, encoding="utf-8") as f:
            assert json.load(f) == {"value": 1}

        # Verify the next tick continues normally instead of crashing again.
        second = _plugin_in(tmp)
        next_result = second.produce()
        assert next_result["value"] == 2

        captured = capsys.readouterr()
        assert "counter state file is corrupt" in captured.err
