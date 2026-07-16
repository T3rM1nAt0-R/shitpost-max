import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

import pytest
from unittest.mock import patch

from extraction_bench_plugin import _extract_json, _score, ExtractionBenchPlugin


def test_extract_json_with_fence():
    raw = '```json\n{"date": "x", "amount": "y"}\n```'
    assert _extract_json(raw) == {"date": "x", "amount": "y"}


def test_extract_json_without_fence():
    raw = '{"date": "x", "amount": "y"}'
    assert _extract_json(raw) == {"date": "x", "amount": "y"}


def test_score_full_match():
    assert _score({"date": "2026-03-14", "amount": "250.00"}, {"date": "2026-03-14", "amount": "250.00"}) == 1.0


def test_score_partial_match():
    assert _score({"date": "wrong", "amount": "250.00"}, {"date": "2026-03-14", "amount": "250.00"}) == 0.5


def test_extract_json_malformed_raises():
    with pytest.raises(Exception):
        _extract_json("not json at all")


def test_produce_returns_none_on_failure(tmp_path, monkeypatch):
    plugin = ExtractionBenchPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    with patch("extraction_bench_plugin._call_ollama", side_effect=OSError("down")):
        assert plugin.produce() is None
