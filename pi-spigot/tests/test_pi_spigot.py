import json
import os
import sys
import tempfile

import pytest

# Tests live in pi-spigot/tests/; the module under test lives in pi-spigot/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pi_spigot  # noqa: E402


# First 30 decimal digits of π, including the leading 3.
KNOWN_PI_30 = "314159265358979323846264338327"


def _plugin_in(tmpdir: str):
    """Return a PiSpigotPlugin whose plugin directory is ``tmpdir``."""
    plugin = pi_spigot.PiSpigotPlugin()
    plugin._plugin_dir = lambda: tmpdir
    return plugin


def test_plugin_metadata():
    assert pi_spigot.PiSpigotPlugin.name == "pi-spigot"
    assert pi_spigot.PiSpigotPlugin.internal is False
    assert pi_spigot.PiSpigotPlugin.commit_template == "pi: digit {n} = {d}"


def test_first_thirty_digits_are_correct():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        digits = [plugin.produce()["digit"] for _ in range(30)]
        assert "".join(str(d) for d in digits) == KNOWN_PI_30


def test_state_persists_across_plugin_instances():
    with tempfile.TemporaryDirectory() as tmp:
        first = _plugin_in(tmp)
        produced = [first.produce()["digit"] for _ in range(10)]

        second = _plugin_in(tmp)
        more = [second.produce()["digit"] for _ in range(10)]

        assert "".join(str(d) for d in produced) == KNOWN_PI_30[:10]
        assert "".join(str(d) for d in more) == KNOWN_PI_30[10:20]


def test_commit_template_formats_correctly():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        result = plugin.produce()
        message = plugin.commit_template.format(**result)
        assert message == f"pi: digit {result['total_digits_seen']} = {result['digit']}"


def test_pi_digits_txt_is_appended():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        for _ in range(12):
            plugin.produce()

        with open(os.path.join(tmp, "pi_digits.txt"), encoding="utf-8") as f:
            contents = f.read()
        assert contents == KNOWN_PI_30[:12]


def test_spigot_state_file_contains_running_state():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        plugin.produce()

        state_path = os.path.join(tmp, "spigot_state.json")
        assert os.path.exists(state_path)
        with open(state_path, encoding="utf-8") as f:
            state = json.load(f)

        for key in ("q", "r", "t", "k", "n", "l"):
            assert key in state
            assert isinstance(state[key], int)
        assert state["tick"] == 1
        assert state["total_digits_seen"] == 1


def test_produce_returns_required_fields():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        result = plugin.produce()
        assert result["digit"] in range(10)
        assert result["tick"] == 1
        assert result["total_digits_seen"] == 1
        assert result["n"] == result["total_digits_seen"]
        assert result["d"] == result["digit"]
        assert "timestamp" in result


def test_atomic_save_does_not_leave_stale_temp_file():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        plugin.produce()

        assert not os.path.exists(os.path.join(tmp, "spigot_state.json.tmp"))
        with open(os.path.join(tmp, "spigot_state.json"), encoding="utf-8") as f:
            state = json.load(f)
        assert state["tick"] == 1


def test_stale_temp_file_is_replaced_by_atomic_save():
    with tempfile.TemporaryDirectory() as tmp:
        stale_path = os.path.join(tmp, "spigot_state.json.tmp")
        with open(stale_path, "w", encoding="utf-8") as f:
            f.write("this is leftover garbage from a crashed write")

        plugin = _plugin_in(tmp)
        plugin.produce()

        assert not os.path.exists(stale_path)
        with open(os.path.join(tmp, "spigot_state.json"), encoding="utf-8") as f:
            state = json.load(f)
        assert state["tick"] == 1


def test_corrupt_state_file_self_heals(capsys):
    with tempfile.TemporaryDirectory() as tmp:
        state_path = os.path.join(tmp, "spigot_state.json")
        with open(state_path, "w", encoding="utf-8") as f:
            f.write("{not valid json")

        plugin = _plugin_in(tmp)
        result = plugin.produce()

        assert result["digit"] == 3
        assert result["tick"] == 1
        assert result["total_digits_seen"] == 1
        with open(state_path, encoding="utf-8") as f:
            state = json.load(f)
        assert state["tick"] == 1
        captured = capsys.readouterr()
        assert "spigot state file is corrupt" in captured.err


def test_state_missing_keys_self_heals(capsys):
    with tempfile.TemporaryDirectory() as tmp:
        state_path = os.path.join(tmp, "spigot_state.json")
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump({"q": 1, "tick": 5}, f)

        plugin = _plugin_in(tmp)
        result = plugin.produce()

        assert result["digit"] == 3
        assert result["tick"] == 1
        assert result["total_digits_seen"] == 1
        captured = capsys.readouterr()
        assert "spigot state missing keys" in captured.err
