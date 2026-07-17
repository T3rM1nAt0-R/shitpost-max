import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from horoscope_gen_plugin import HoroscopeGenPlugin


def test_cycles_through_all_12_signs_in_zodiac_order(tmp_path, monkeypatch):
    plugin = HoroscopeGenPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen = []
    for _ in range(12):
        result = plugin.produce()
        seen.append(result["sign"])

    assert seen == [s[0] for s in HoroscopeGenPlugin._SIGNS]
    assert seen[0] == "Aries"


def test_wraps_around_after_pisces(tmp_path, monkeypatch):
    plugin = HoroscopeGenPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    for _ in range(12):
        plugin.produce()
    result = plugin.produce()
    assert result["sign"] == "Aries"
