import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

import pytest

from mars_weather_plugin import _parse

FIXTURE = {
    "sol_keys": ["675", "676", "677", "678", "679", "680", "681"],
    "681": {
        "AT": {"av": -62.434, "ct": 88778, "mn": -95.447, "mx": -4.444},
        "Season": "fall",
    },
}


def test_parse_matches_ground_truth():
    result = _parse(FIXTURE)
    assert result == {
        "sol": "681",
        "avg_temp_c": -62.434,
        "min_temp_c": -95.447,
        "max_temp_c": -4.444,
        "season": "fall",
    }


def test_empty_sol_keys_raises():
    with pytest.raises(ValueError):
        _parse({"sol_keys": []})


def test_produce_returns_none_on_fetch_failure(monkeypatch):
    from mars_weather_plugin import MarsWeatherPlugin
    import urllib.request

    def _raise(*args, **kwargs):
        raise OSError("network unreachable")

    monkeypatch.setattr(urllib.request, "urlopen", _raise)
    plugin = MarsWeatherPlugin()
    assert plugin.produce() is None
