import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

import pytest

from aurora_forecast_plugin import _parse


def test_parse_matches_ground_truth():
    readings = [{"time_tag": "2026-07-16T15:00:00", "Kp": 1.0, "a_running": 4, "station_count": 6}]
    result = _parse(readings)
    assert result == {
        "kp_index": 1.0,
        "time_tag": "2026-07-16T15:00:00",
        "aurora_likelihood": "unlikely",
    }


def test_likelihood_thresholds():
    assert _parse([{"time_tag": "t", "Kp": 3.9}])["aurora_likelihood"] == "unlikely"
    assert _parse([{"time_tag": "t", "Kp": 4.0}])["aurora_likelihood"] == "possible at high latitudes"
    assert _parse([{"time_tag": "t", "Kp": 6.5}])["aurora_likelihood"] == "likely at mid latitudes"


def test_empty_readings_raises():
    with pytest.raises(ValueError):
        _parse([])


def test_produce_returns_none_on_fetch_failure(monkeypatch):
    from aurora_forecast_plugin import AuroraForecastPlugin
    import urllib.request

    def _raise(*args, **kwargs):
        raise OSError("network unreachable")

    monkeypatch.setattr(urllib.request, "urlopen", _raise)
    plugin = AuroraForecastPlugin()
    assert plugin.produce() is None
