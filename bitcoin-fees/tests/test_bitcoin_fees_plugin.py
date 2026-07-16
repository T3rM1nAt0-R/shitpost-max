import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from bitcoin_fees_plugin import _parse

FIXTURE = {"fastestFee": 2, "halfHourFee": 1, "hourFee": 1, "economyFee": 1, "minimumFee": 1}


def test_parse_matches_ground_truth():
    result = _parse(FIXTURE)
    assert result == {
        "fastest_fee": 2,
        "half_hour_fee": 1,
        "hour_fee": 1,
        "economy_fee": 1,
        "minimum_fee": 1,
    }


def test_produce_returns_none_on_fetch_failure(monkeypatch):
    from bitcoin_fees_plugin import BitcoinFeesPlugin
    import urllib.request

    def _raise(*args, **kwargs):
        raise OSError("network unreachable")

    monkeypatch.setattr(urllib.request, "urlopen", _raise)
    plugin = BitcoinFeesPlugin()
    assert plugin.produce() is None
