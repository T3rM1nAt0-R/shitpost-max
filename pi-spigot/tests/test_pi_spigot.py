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


def test_save_state_survives_state_ints_past_default_str_digit_limit(tmp_path):
    """The spigot's q/r/t/l state ints grow with every tick and are
    persisted via json.dump. Python 3.11+'s default int->str conversion
    limit is 4300 digits (CVE-2020-10735 guard) -- this actually broke
    pi-spigot in production on 2026-07-14 after 860 ticks: every save
    since threw ValueError and silently failed (caught by run_tick's
    per-plugin exception isolation), so the plugin looked frozen rather
    than erroring. harness.shitpost_base disables the limit at import
    time since these are our own algorithm's state, not untrusted input;
    confirm a state well past that threshold still round-trips."""
    plugin = _plugin_in(str(tmp_path))
    huge_int = int("7" * 5000)
    state = {
        "q": huge_int, "r": huge_int, "t": huge_int, "k": 1,
        "n": 3, "l": huge_int, "tick": 860, "total_digits_seen": 860,
    }
    plugin._save_state(str(tmp_path), state)
    reloaded = plugin._load_state(str(tmp_path))
    assert reloaded["q"] == huge_int
