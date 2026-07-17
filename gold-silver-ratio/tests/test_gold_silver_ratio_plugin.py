import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from gold_silver_ratio_plugin import _parse

GOLD_FIXTURE = {"price": 3975.800049, "symbol": "XAU"}
SILVER_FIXTURE = {"price": 55.661999, "symbol": "XAG"}


def test_parse_matches_ground_truth():
    result = _parse(GOLD_FIXTURE, SILVER_FIXTURE)
    assert result["gold_price"] == 3975.800049
    assert result["silver_price"] == 55.661999
    assert result["ratio"] == 71.43


def test_produce_returns_none_on_fetch_failure(monkeypatch):
    from gold_silver_ratio_plugin import GoldSilverRatioPlugin
    import urllib.request

    def _raise(*args, **kwargs):
        raise OSError("network unreachable")

    monkeypatch.setattr(urllib.request, "urlopen", _raise)
    plugin = GoldSilverRatioPlugin()
    assert plugin.produce() is None
