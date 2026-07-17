import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

import pytest
from unittest.mock import patch

from wikipedia_trending_plugin import _parse, WikipediaTrendingPlugin, TOP_N

FIXTURE = {
    "items": [
        {
            "articles": [
                {"article": "Main_Page", "views": 8825504},
                {"article": "Special:Search", "views": 1325339},
                {"article": "Wikipedia:Featured_pictures", "views": 700927},
                {"article": "The_Odyssey_(2026_film)", "views": 614398},
                {"article": "Lionel_Messi", "views": 432207},
                {"article": "Falkland_Islands", "views": 428400},
                {"article": "2026_FIFA_World_Cup", "views": 338930},
                {"article": "Lamine_Yamal", "views": 292389},
            ]
        }
    ]
}


def test_parse_excludes_meta_pages_and_matches_ground_truth():
    result = _parse(FIXTURE)
    assert result == [
        ("The_Odyssey_(2026_film)", 614398),
        ("Lionel_Messi", 432207),
        ("Falkland_Islands", 428400),
        ("2026_FIFA_World_Cup", 338930),
        ("Lamine_Yamal", 292389),
    ]


def test_parse_raises_if_too_few_after_filtering():
    small_fixture = {"items": [{"articles": [{"article": "Main_Page", "views": 1}, {"article": "Real_Article", "views": 2}]}]}
    with pytest.raises(ValueError):
        _parse(small_fixture)


def test_index_cycles_across_ticks(tmp_path, monkeypatch):
    import json as json_module
    import urllib.request

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json_module.dumps(FIXTURE).encode()

    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: FakeResponse())

    plugin = WikipediaTrendingPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    result = plugin.produce()
    assert result == {
        "rank": 1, "article": "The_Odyssey_(2026_film)", "views": 614398, "date": result["date"],
    }

    for _ in range(TOP_N - 1):
        result = plugin.produce()
    assert result["rank"] == TOP_N
    assert result["article"] == "Lamine_Yamal"

    result = plugin.produce()
    assert result["rank"] == 1
    assert result["article"] == "The_Odyssey_(2026_film)"


def test_produce_returns_none_on_fetch_failure(tmp_path, monkeypatch):
    import urllib.request

    plugin = WikipediaTrendingPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    def _raise(*args, **kwargs):
        raise OSError("network unreachable")

    monkeypatch.setattr(urllib.request, "urlopen", _raise)
    assert plugin.produce() is None
