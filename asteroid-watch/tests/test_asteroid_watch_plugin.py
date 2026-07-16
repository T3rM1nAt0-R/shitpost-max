import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

import pytest

from asteroid_watch_plugin import _parse

FIXTURE = {
    "element_count": 5,
    "near_earth_objects": {
        "2026-07-16": [
            {
                "name": "(2009 DB1)",
                "close_approach_data": [{"miss_distance": {"kilometers": "69118723.009667573"}}],
                "is_potentially_hazardous_asteroid": False,
            },
            {
                "name": "(2009 HA21)",
                "close_approach_data": [{"miss_distance": {"kilometers": "53400709.512865816"}}],
                "is_potentially_hazardous_asteroid": True,
            },
        ]
    },
}


def test_parse_matches_ground_truth():
    result = _parse(FIXTURE)
    assert result == {
        "element_count": 5,
        "closest_name": "(2009 HA21)",
        "closest_miss_km": 53400709.512865816,
        "closest_hazardous": True,
    }


def test_empty_objects_raises():
    fixture = {"element_count": 0, "near_earth_objects": {"2026-07-16": []}}
    with pytest.raises(ValueError):
        _parse(fixture)


def test_produce_returns_none_on_fetch_failure(monkeypatch):
    from asteroid_watch_plugin import AsteroidWatchPlugin
    import urllib.request

    def _raise(*args, **kwargs):
        raise OSError("network unreachable")

    monkeypatch.setattr(urllib.request, "urlopen", _raise)
    plugin = AsteroidWatchPlugin()
    assert plugin.produce() is None
