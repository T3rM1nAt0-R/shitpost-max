import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

import pytest

from stackoverflow_tags_plugin import _parse, StackoverflowTagsPlugin, TAGS

FIXTURE = {
    "items": [
        {"has_synonyms": True, "is_moderator_only": False, "is_required": False, "count": 2219702, "name": "python"}
    ],
    "has_more": False,
}


def test_parse_matches_ground_truth():
    result = _parse(FIXTURE)
    assert result == {"tag": "python", "count": 2219702}


def test_empty_items_raises():
    with pytest.raises(ValueError):
        _parse({"items": []})


def test_index_advances_only_on_success(tmp_path, monkeypatch):
    import json as json_module
    import urllib.request

    class FakeResponse:
        def __init__(self, tag):
            self._tag = tag

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            fixture = {"items": [{"count": 2219702, "name": self._tag}], "has_more": False}
            return json_module.dumps(fixture).encode()

    def _fake_urlopen(request, *a, **k):
        # request is the URL string built from ENDPOINT_TEMPLATE.format(tag=...)
        for candidate in TAGS:
            if f"/{candidate}/" in request:
                return FakeResponse(candidate)
        raise AssertionError(f"unexpected URL: {request}")

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)

    plugin = StackoverflowTagsPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    result = plugin.produce()
    assert result == {"tag": TAGS[0], "count": 2219702}

    def _raise(*args, **kwargs):
        raise OSError("network unreachable")

    monkeypatch.setattr(urllib.request, "urlopen", _raise)
    assert plugin.produce() is None

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)
    result = plugin.produce()
    assert result["tag"] == TAGS[1]
