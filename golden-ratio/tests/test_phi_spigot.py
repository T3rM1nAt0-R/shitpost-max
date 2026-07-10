import json
import os
import sys
import tempfile

import pytest

# Tests live in golden-ratio/tests/; the module under test lives in golden-ratio/,
# which in turn imports `harness.shitpost_base` from the repo root. Insert both
# so the tests are runnable regardless of cwd (previously only golden-ratio/ was
# added, which worked only by accident when pytest's cwd-on-sys.path happened to
# already include the repo root - found in DeepSeek review, 2026-07-10).
_PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

import phi_spigot  # noqa: E402


def _known_phi_digits(count: int) -> str:
    """Return the first ``count`` significant decimal digits of φ."""
    from decimal import Decimal, getcontext

    getcontext().prec = max(count + 20, 50)
    phi = (1 + Decimal(5).sqrt()) / 2
    return str(phi).replace(".", "")[:count]


def _plugin_in(tmpdir: str):
    """Return a PhiSpigotPlugin whose plugin directory is ``tmpdir``."""
    plugin = phi_spigot.PhiSpigotPlugin()
    plugin._plugin_dir = lambda: tmpdir
    return plugin


def test_plugin_metadata():
    assert phi_spigot.PhiSpigotPlugin.name == "golden-ratio"
    assert phi_spigot.PhiSpigotPlugin.internal is False
    assert (
        phi_spigot.PhiSpigotPlugin.commit_template
        == "φ: digit {total_digits_seen} = {digit} (convergent {convergent_n})"
    )


def test_first_hundred_digits_are_correct():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        digits = [plugin.produce()["digit"] for _ in range(100)]
        produced = "".join(str(d) for d in digits)
        assert produced == _known_phi_digits(100)


def test_state_persists_across_plugin_instances():
    with tempfile.TemporaryDirectory() as tmp:
        first = _plugin_in(tmp)
        produced = [first.produce()["digit"] for _ in range(10)]

        second = _plugin_in(tmp)
        more = [second.produce()["digit"] for _ in range(10)]

        assert "".join(str(d) for d in produced) == _known_phi_digits(10)
        assert "".join(str(d) for d in more) == _known_phi_digits(20)[10:20]


def test_commit_template_formats_correctly():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        result = plugin.produce()
        message = plugin.commit_template.format(**result)
        assert message == (
            f"φ: digit {result['total_digits_seen']} = {result['digit']} "
            f"(convergent {result['convergent_n']})"
        )


def test_phi_digits_txt_is_appended():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        for _ in range(12):
            plugin.produce()

        with open(os.path.join(tmp, "phi_digits.txt"), encoding="utf-8") as f:
            contents = f.read()
        assert contents == _known_phi_digits(12)


def test_spigot_state_file_contains_running_state():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        plugin.produce()

        state_path = os.path.join(tmp, "spigot_state.json")
        assert os.path.exists(state_path)
        with open(state_path, encoding="utf-8") as f:
            state = json.load(f)

        for key in ("p_prev", "q_prev", "p_curr", "q_curr", "n"):
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
        assert isinstance(result["convergent_n"], int)
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

        assert result["digit"] == 1
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
            json.dump({"p_prev": 1, "tick": 5}, f)

        plugin = _plugin_in(tmp)
        result = plugin.produce()

        assert result["digit"] == 1
        assert result["tick"] == 1
        assert result["total_digits_seen"] == 1
        captured = capsys.readouterr()
        assert "spigot state missing keys" in captured.err
