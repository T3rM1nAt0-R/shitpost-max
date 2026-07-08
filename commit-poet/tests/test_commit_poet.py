import json
import os
import sys
import tempfile
import urllib.error
from unittest import mock

import pytest

# Tests live in commit-poet/tests/; the module under test lives in commit-poet/.
# The repo root is also needed so the shared ``harness`` package is importable.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import poet  # noqa: E402


_FALLBACK_LINE = poet._FALLBACK_LINE


def _plugin_in(tmpdir: str, **kwargs):
    """Return a CommitPoetPlugin whose plugin directory is ``tmpdir``."""
    plugin = poet.CommitPoetPlugin(**kwargs)
    plugin._plugin_dir = lambda: tmpdir
    return plugin


def _mock_ollama_response(text: str, token_count: int = 7):
    """Return a mock that behaves like a successful urlopen response."""
    resp = mock.Mock()
    resp.read.return_value = json.dumps(
        {"response": text, "eval_count": token_count}
    ).encode("utf-8")
    resp.__enter__ = mock.Mock(return_value=resp)
    resp.__exit__ = mock.Mock(return_value=False)
    return resp


def _read_poem_lines(tmpdir: str) -> list[str]:
    path = os.path.join(tmpdir, "poem.txt")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f]


def _read_poem_log(tmpdir: str) -> list[dict]:
    path = os.path.join(tmpdir, "poem_log.jsonl")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def test_plugin_metadata():
    assert poet.CommitPoetPlugin.name == "commit-poet"
    assert poet.CommitPoetPlugin.internal is False
    assert poet.CommitPoetPlugin.commit_template == "{line}"


def test_defaults_match_design():
    plugin = poet.CommitPoetPlugin()
    assert plugin.ollama_url == "http://localhost:1601"
    assert plugin.ollama_model == "qwen2.5:7b"
    assert plugin.context_lines == 10


def test_constructor_overrides_defaults():
    plugin = poet.CommitPoetPlugin(
        ollama_url="http://other:1234",
        ollama_model="mistral:7b",
        context_lines=3,
        timeout=1.0,
    )
    assert plugin.ollama_url == "http://other:1234"
    assert plugin.ollama_model == "mistral:7b"
    assert plugin.context_lines == 3
    assert plugin.timeout == 1.0


def test_build_prompt_includes_recent_lines():
    with tempfile.TemporaryDirectory() as tmp:
        poem_path = os.path.join(tmp, "poem.txt")
        with open(poem_path, "w", encoding="utf-8") as f:
            f.write("line one\nline two\nline three\n")

        plugin = _plugin_in(tmp, context_lines=2)
        recent = plugin._read_recent_lines(tmp)
        prompt = plugin._build_prompt(recent)

        assert "line two" in prompt
        assert "line three" in prompt
        assert "line one" not in prompt
        assert "under 72 characters" in prompt
        assert "do not repeat" in prompt.lower()


def test_build_prompt_shows_empty_context_on_first_run():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp, context_lines=5)
        recent = plugin._read_recent_lines(plugin._plugin_dir())
        prompt = plugin._build_prompt(recent)

        assert "(none yet" in prompt
        assert "Recent lines:" in prompt


def test_produce_appends_poem_line_and_log():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        with mock.patch.object(
            poet.urllib.request, "urlopen", return_value=_mock_ollama_response("the moon whispers")
        ):
            result = plugin.produce()

        assert result["line"] == "the moon whispers"
        assert result["fallback_used"] is False
        assert result["model"] == plugin.ollama_model
        assert result["token_count"] == 7

        lines = _read_poem_lines(tmp)
        assert lines == ["the moon whispers"]

        log = _read_poem_log(tmp)
        assert len(log) == 1
        assert log[0]["line"] == "the moon whispers"
        assert log[0]["fallback_used"] is False
        assert log[0]["model"] == plugin.ollama_model
        assert log[0]["token_count"] == 7
        assert "timestamp" in log[0]


def test_fallback_on_connection_error():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        with mock.patch.object(
            poet.urllib.request,
            "urlopen",
            side_effect=urllib.error.URLError("refused"),
        ):
            result = plugin.produce()

        assert result["line"] == _FALLBACK_LINE
        assert result["fallback_used"] is True
        assert result["token_count"] is None

        lines = _read_poem_lines(tmp)
        assert lines == [_FALLBACK_LINE]

        log = _read_poem_log(tmp)
        assert log[0]["fallback_used"] is True


def test_fallback_on_empty_response():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        with mock.patch.object(
            poet.urllib.request,
            "urlopen",
            return_value=_mock_ollama_response("   \n  "),
        ):
            result = plugin.produce()

        assert result["line"] == _FALLBACK_LINE
        assert result["fallback_used"] is True

        lines = _read_poem_lines(tmp)
        assert lines == [_FALLBACK_LINE]


def test_72_char_truncation():
    long_line = "a" * 100
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        with mock.patch.object(
            poet.urllib.request,
            "urlopen",
            return_value=_mock_ollama_response(long_line),
        ):
            result = plugin.produce()

        assert len(result["line"]) == 72
        assert result["line"] == "a" * 72
        assert _read_poem_lines(tmp)[0] == "a" * 72


def test_multiline_response_uses_first_non_empty_line():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        with mock.patch.object(
            poet.urllib.request,
            "urlopen",
            return_value=_mock_ollama_response("\n\nsecond verse\nthird verse"),
        ):
            result = plugin.produce()

        assert result["line"] == "second verse"


@pytest.mark.parametrize(
    "raw_response,expected_line",
    [
        ("> the moon whispers", "the moon whispers"),
        ("- the moon whispers", "the moon whispers"),
        ("* the moon whispers", "the moon whispers"),
        ("1. the moon whispers", "the moon whispers"),
        ("12) the moon whispers", "the moon whispers"),
        ('"the moon whispers"', "the moon whispers"),
        ("'the moon whispers'", "the moon whispers"),
        ("`the moon whispers`", "the moon whispers"),
        ("- `the moon whispers`", "the moon whispers"),
    ],
)
def test_markdown_wrapped_response_is_cleaned_before_storage(raw_response, expected_line):
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        with mock.patch.object(
            poet.urllib.request,
            "urlopen",
            return_value=_mock_ollama_response(raw_response),
        ):
            result = plugin.produce()

        assert result["line"] == expected_line
        assert _read_poem_lines(tmp) == [expected_line]


def test_blank_lines_skipped_when_building_context_window():
    with tempfile.TemporaryDirectory() as tmp:
        poem_path = os.path.join(tmp, "poem.txt")
        with open(poem_path, "w", encoding="utf-8") as f:
            f.write("line one\n\n  \nline two\nline three\n\n")

        plugin = _plugin_in(tmp, context_lines=2)
        recent = plugin._read_recent_lines(tmp)

        assert recent == ["line two", "line three"]


def test_repeat_detection_retries_once():
    with tempfile.TemporaryDirectory() as tmp:
        poem_path = os.path.join(tmp, "poem.txt")
        with open(poem_path, "w", encoding="utf-8") as f:
            f.write("old line\n")

        plugin = _plugin_in(tmp, context_lines=3)
        with mock.patch.object(
            poet.urllib.request,
            "urlopen",
            side_effect=[
                _mock_ollama_response("old line"),
                _mock_ollama_response("fresh line"),
            ],
        ):
            result = plugin.produce()

        assert result["line"] == "fresh line"
        assert result["fallback_used"] is False
        lines = _read_poem_lines(tmp)
        assert lines == ["old line", "fresh line"]


def test_repeated_line_still_appended_after_failed_retry():
    with tempfile.TemporaryDirectory() as tmp:
        poem_path = os.path.join(tmp, "poem.txt")
        with open(poem_path, "w", encoding="utf-8") as f:
            f.write("old line\n")

        plugin = _plugin_in(tmp, context_lines=3)
        with mock.patch.object(
            poet.urllib.request,
            "urlopen",
            side_effect=[
                _mock_ollama_response("old line"),
                _mock_ollama_response("old line"),
            ],
        ):
            result = plugin.produce()

        assert result["line"] == "old line"
        assert result["fallback_used"] is False
        lines = _read_poem_lines(tmp)
        assert lines == ["old line", "old line"]


def test_prompt_sent_to_ollama_uses_expected_model_and_url():
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp, ollama_model="qwen2.5:7b")
        with mock.patch.object(
            poet.urllib.request, "urlopen", return_value=_mock_ollama_response("a line")
        ) as mock_urlopen:
            plugin.produce()

        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "http://localhost:1601/api/generate"
        assert req.method == "POST"
        body = json.loads(req.data)
        assert body["model"] == "qwen2.5:7b"
        assert body["stream"] is False
        assert "prompt" in body


def test_context_lines_env_respected(monkeypatch):
    monkeypatch.setenv("CONTEXT_LINES", "4")
    plugin = poet.CommitPoetPlugin()
    assert plugin.context_lines == 4


@pytest.mark.integration
def test_real_ollama_generates_non_empty_line():
    """Actually call the local Ollama instance; skip if it is not reachable.

    This test is intentionally conditional: if Ollama is down, the plugin is
    designed to fall back, so a fallback result is treated as a skip rather
    than a failure for this live-integration check.
    """
    with tempfile.TemporaryDirectory() as tmp:
        plugin = _plugin_in(tmp)
        result = plugin.produce()

        if result["fallback_used"]:
            pytest.skip("Ollama did not return a generated line; skipping live integration test")

        assert result["line"]
        assert isinstance(result["line"], str)
        assert len(result["line"]) <= 72
        assert result["token_count"] is not None
        assert _read_poem_lines(tmp) == [result["line"]]
