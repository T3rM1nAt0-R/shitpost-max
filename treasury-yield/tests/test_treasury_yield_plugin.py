import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from treasury_yield_plugin import _parse

FIXTURE_CSV = (
    'Date,"1 Mo","1.5 Month","2 Mo","3 Mo","4 Mo","6 Mo","1 Yr","2 Yr","3 Yr","5 Yr","7 Yr","10 Yr","20 Yr","30 Yr"\n'
    '07/16/2026,3.76,3.75,3.81,3.84,3.90,3.94,3.99,4.16,4.20,4.28,4.41,4.57,5.09,5.09\n'
)


def test_parse_matches_ground_truth():
    result = _parse(FIXTURE_CSV)
    assert result == {"date": "07/16/2026", "yield_10yr": 4.57}


def test_produce_returns_none_on_fetch_failure(monkeypatch):
    from treasury_yield_plugin import TreasuryYieldPlugin
    import urllib.request

    def _raise(*args, **kwargs):
        raise OSError("network unreachable")

    monkeypatch.setattr(urllib.request, "urlopen", _raise)
    plugin = TreasuryYieldPlugin()
    assert plugin.produce() is None
