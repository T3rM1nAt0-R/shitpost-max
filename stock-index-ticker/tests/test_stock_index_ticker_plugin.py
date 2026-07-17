import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from stock_index_ticker_plugin import _parse

FIXTURE = {
    "chart": {
        "result": [
            {"meta": {"symbol": "^GSPC", "regularMarketPrice": 7533.77, "previousClose": 7572.4}}
        ]
    }
}


def test_parse_matches_ground_truth():
    result = _parse(FIXTURE)
    assert result["symbol"] == "^GSPC"
    assert result["price"] == 7533.77
    assert result["previous_close"] == 7572.4
    assert result["pct_change"] == -0.51


def test_produce_returns_none_on_fetch_failure(monkeypatch):
    from stock_index_ticker_plugin import StockIndexTickerPlugin
    import urllib.request

    def _raise(*args, **kwargs):
        raise OSError("network unreachable")

    monkeypatch.setattr(urllib.request, "urlopen", _raise)
    plugin = StockIndexTickerPlugin()
    assert plugin.produce() is None
