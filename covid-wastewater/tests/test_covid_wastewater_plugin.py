import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

import pytest

from covid_wastewater_plugin import _parse

FIXTURE = [
    {
        "wwtp_jurisdiction": "Maryland",
        "wwtp_id": "2952",
        "county_names": "Montgomery",
        "date_start": "2025-02-04",
        "date_end": "2025-02-18",
        "percentile": "81.0",
    }
]


def test_parse_matches_ground_truth():
    result = _parse(FIXTURE)
    assert result == {
        "jurisdiction": "Maryland",
        "percentile": 81.0,
        "date_start": "2025-02-04",
        "date_end": "2025-02-18",
    }


def test_empty_records_raises():
    with pytest.raises(ValueError):
        _parse([])


def test_produce_returns_none_on_fetch_failure(monkeypatch):
    from covid_wastewater_plugin import CovidWastewaterPlugin
    import urllib.request

    def _raise(*args, **kwargs):
        raise OSError("network unreachable")

    monkeypatch.setattr(urllib.request, "urlopen", _raise)
    plugin = CovidWastewaterPlugin()
    assert plugin.produce() is None
