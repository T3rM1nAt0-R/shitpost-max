import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from mempool_watch_plugin import _parse

FIXTURE = {"count": 105272, "vsize": 46025361, "total_fee": 11198059, "fee_histogram": [[1.0, 100]]}


def test_parse_ignores_histogram_and_matches_ground_truth():
    result = _parse(FIXTURE)
    assert result == {"tx_count": 105272, "vsize": 46025361, "total_fee": 11198059}


def test_produce_returns_none_on_fetch_failure(monkeypatch):
    from mempool_watch_plugin import MempoolWatchPlugin
    import urllib.request

    def _raise(*args, **kwargs):
        raise OSError("network unreachable")

    monkeypatch.setattr(urllib.request, "urlopen", _raise)
    plugin = MempoolWatchPlugin()
    assert plugin.produce() is None
