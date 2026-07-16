import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from happy_numbers_plugin import HappyNumbersPlugin

# Known-correct sequence of happy numbers (OEIS A007770).
KNOWN_HAPPY_NUMBERS = [1, 7, 10, 13, 19, 23, 28, 31]


def test_is_happy_matches_known_values():
    plugin = HappyNumbersPlugin()
    for n in KNOWN_HAPPY_NUMBERS:
        assert plugin._is_happy(n)
    # A couple of known-unhappy numbers.
    assert not plugin._is_happy(2)
    assert not plugin._is_happy(4)


def test_finds_happy_numbers_in_order(tmp_path, monkeypatch):
    plugin = HappyNumbersPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    found = []
    while len(found) < len(KNOWN_HAPPY_NUMBERS):
        result = plugin.produce()
        if result is not None:
            found.append(result["happy_number"])

    assert found == KNOWN_HAPPY_NUMBERS


def test_never_emits_an_unhappy_number(tmp_path, monkeypatch):
    plugin = HappyNumbersPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    for _ in range(20):
        result = plugin.produce()
        if result is not None:
            assert plugin._is_happy(result["happy_number"])
