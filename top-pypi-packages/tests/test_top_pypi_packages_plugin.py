import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

import pytest

from top_pypi_packages_plugin import _parse, TopPypiPackagesPlugin

FIXTURE = {
    "rows": [
        {"project": "boto3", "download_count": 3584010793},
        {"project": "packaging", "download_count": 2097243437},
        {"project": "urllib3", "download_count": 1730712189},
        {"project": "certifi", "download_count": 1713421229},
        {"project": "idna", "download_count": 1660427957},
    ]
}


def test_parse_matches_ground_truth():
    result = _parse(FIXTURE)
    assert result == [
        ("boto3", 3584010793),
        ("packaging", 2097243437),
        ("urllib3", 1730712189),
        ("certifi", 1713421229),
        ("idna", 1660427957),
    ]


def test_too_few_rows_raises():
    with pytest.raises(ValueError):
        _parse({"rows": [{"project": "a", "download_count": 1}]})


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

    plugin = TopPypiPackagesPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    result = plugin.produce()
    assert result == {"rank": 1, "project": "boto3", "download_count": 3584010793}

    for _ in range(4):
        result = plugin.produce()
    assert result == {"rank": 5, "project": "idna", "download_count": 1660427957}

    result = plugin.produce()
    assert result == {"rank": 1, "project": "boto3", "download_count": 3584010793}
