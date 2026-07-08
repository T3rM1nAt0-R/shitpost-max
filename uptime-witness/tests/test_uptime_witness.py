import http.client
import json
import os
import sys
import tempfile
import threading
import time
import urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

import pytest

# Tests live in uptime-witness/tests/; the module under test lives in
# uptime-witness/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uptime_witness  # noqa: E402


def _plugin_with_tools_json(path: str | None = None):
    """Return a plugin configured for the given tools.json path."""
    plugin = uptime_witness.UptimeWitnessPlugin(tools_json_path=path)
    return plugin


def test_plugin_metadata():
    assert uptime_witness.UptimeWitnessPlugin.name == "uptime-witness"
    assert uptime_witness.UptimeWitnessPlugin.internal is True
    assert uptime_witness.UptimeWitnessPlugin.commit_template == "uptime: {ok}/{total} OK"


def test_produce_returns_tuple_shape():
    plugin = _plugin_with_tools_json()
    with mock.patch.object(uptime_witness.urllib.request, "urlopen") as mock_urlopen:
        mock_resp = mock.Mock()
        mock_resp.getcode.return_value = 200
        mock_resp.read.return_value = b"ok"
        mock_urlopen.return_value.__enter__ = mock.Mock(return_value=mock_resp)
        mock_urlopen.return_value.__exit__ = mock.Mock(return_value=False)

        result = plugin.produce()

    assert isinstance(result, tuple)
    assert len(result) == 2
    summary, details = result
    assert isinstance(summary, dict)
    assert isinstance(details, list)
    assert summary == {"ok": len(details), "total": len(details)}
    for detail in details:
        assert isinstance(detail, dict)
        assert "service" in detail
        assert "url" in detail
        assert "status_code" in detail
        assert "response_ms" in detail
        assert "ok" in detail
        assert detail["ok"] is True


def test_commit_template_formats_against_summary():
    plugin = _plugin_with_tools_json()
    with mock.patch.object(uptime_witness.urllib.request, "urlopen") as mock_urlopen:
        mock_resp = mock.Mock()
        mock_resp.getcode.return_value = 200
        mock_resp.read.return_value = b"ok"
        mock_urlopen.return_value.__enter__ = mock.Mock(return_value=mock_resp)
        mock_urlopen.return_value.__exit__ = mock.Mock(return_value=False)

        summary, _details = plugin.produce()

    message = plugin.commit_template.format(**summary)
    assert message == f"uptime: {summary['ok']}/{summary['total']} OK"


def test_non_200_response_recorded_not_ok():
    plugin = _plugin_with_tools_json()
    with mock.patch.object(
        uptime_witness.urllib.request, "urlopen", side_effect=urllib.error.HTTPError(
            url="http://localhost:1001/health",
            code=502,
            msg="Bad Gateway",
            hdrs={},
            fp=None,
        )
    ):
        summary, details = plugin.produce()

    assert summary["total"] > 0
    assert summary["ok"] == 0
    assert all(d["ok"] is False for d in details)
    assert all(d["status_code"] == 502 for d in details)


def test_urlerror_recorded_not_ok():
    plugin = _plugin_with_tools_json()
    with mock.patch.object(
        uptime_witness.urllib.request, "urlopen", side_effect=urllib.error.URLError("refused")
    ):
        summary, details = plugin.produce()

    assert summary["total"] > 0
    assert summary["ok"] == 0
    assert all(d["ok"] is False for d in details)
    assert all(d["status_code"] is None for d in details)


def test_timeout_recorded_not_ok():
    plugin = _plugin_with_tools_json()
    with mock.patch.object(
        uptime_witness.urllib.request, "urlopen", side_effect=TimeoutError("timed out")
    ):
        summary, details = plugin.produce()

    assert summary["total"] > 0
    assert summary["ok"] == 0
    assert all(d["ok"] is False for d in details)
    assert all(d["status_code"] is None for d in details)


def test_oserror_recorded_not_ok():
    plugin = _plugin_with_tools_json()
    with mock.patch.object(
        uptime_witness.urllib.request, "urlopen", side_effect=OSError("no route")
    ):
        summary, details = plugin.produce()

    assert summary["total"] > 0
    assert summary["ok"] == 0
    assert all(d["ok"] is False for d in details)


def test_missing_tools_json_uses_fallback():
    with tempfile.TemporaryDirectory() as tmp:
        missing_path = os.path.join(tmp, "does-not-exist.json")
        plugin = _plugin_with_tools_json(missing_path)
        with mock.patch.object(uptime_witness.urllib.request, "urlopen") as mock_urlopen:
            mock_resp = mock.Mock()
            mock_resp.getcode.return_value = 200
            mock_resp.read.return_value = b"ok"
            mock_urlopen.return_value.__enter__ = mock.Mock(return_value=mock_resp)
            mock_urlopen.return_value.__exit__ = mock.Mock(return_value=False)

            summary, details = plugin.produce()

        names = {d["service"] for d in details}
        fallback_names = {s["name"] for s in uptime_witness._FALLBACK_SERVICES}
        assert names == fallback_names
        assert summary == {"ok": len(details), "total": len(details)}


def test_custom_tools_json_overrides_default():
    with tempfile.TemporaryDirectory() as tmp:
        tools_path = os.path.join(tmp, "tools.json")
        with open(tools_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "tools": [
                        {"name": "alpha", "port": 9999, "live": True},
                        {"name": "beta", "port": 9998, "live": False},
                    ]
                },
                f,
            )

        plugin = _plugin_with_tools_json(tools_path)
        with mock.patch.object(uptime_witness.urllib.request, "urlopen") as mock_urlopen:
            mock_resp = mock.Mock()
            mock_resp.getcode.return_value = 200
            mock_resp.read.return_value = b"ok"
            mock_urlopen.return_value.__enter__ = mock.Mock(return_value=mock_resp)
            mock_urlopen.return_value.__exit__ = mock.Mock(return_value=False)

            summary, details = plugin.produce()

        assert summary["total"] == 1
        assert details[0]["service"] == "alpha"
        assert details[0]["url"] == "http://localhost:9999/health"


def test_response_ms_is_non_negative():
    plugin = _plugin_with_tools_json()
    with mock.patch.object(uptime_witness.urllib.request, "urlopen") as mock_urlopen:
        mock_resp = mock.Mock()
        mock_resp.getcode.return_value = 200
        mock_resp.read.return_value = b"ok"
        mock_urlopen.return_value.__enter__ = mock.Mock(return_value=mock_resp)
        mock_urlopen.return_value.__exit__ = mock.Mock(return_value=False)

        _summary, details = plugin.produce()

    assert all(isinstance(d["response_ms"], int) for d in details)
    assert all(d["response_ms"] >= 0 for d in details)


class _HealthHandler(BaseHTTPRequestHandler):
    """Tiny handler that answers 200 on /health and 404 elsewhere."""

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, _format, *args):
        # Silence server logs during tests.
        pass


@pytest.mark.skipif(
    os.environ.get("SKIP_INTEGRATION") == "1",
    reason="integration tests disabled by SKIP_INTEGRATION",
)
def test_real_loopback_health_endpoint():
    """Start a real HTTP server on localhost and verify it is seen as OK."""
    server = HTTPServer(("127.0.0.1", 0), _HealthHandler)
    port = server.server_address[1]

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            tools_path = os.path.join(tmp, "tools.json")
            with open(tools_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "tools": [
                            {"name": "test-service", "port": port, "live": True},
                        ]
                    },
                    f,
                )

            plugin = _plugin_with_tools_json(tools_path)
            summary, details = plugin.produce()

            assert summary == {"ok": 1, "total": 1}
            assert len(details) == 1
            assert details[0]["service"] == "test-service"
            assert details[0]["status_code"] == 200
            assert details[0]["ok"] is True
            assert details[0]["response_ms"] >= 0
    finally:
        server.shutdown()
        server.server_close()


def _ok_mock_response():
    """Return a mock that behaves like a successful urlopen response."""
    resp = mock.Mock()
    resp.getcode.return_value = 200
    resp.read.return_value = b"ok"
    resp.__enter__ = mock.Mock(return_value=resp)
    resp.__exit__ = mock.Mock(return_value=False)
    return resp


def test_http_client_exception_does_not_crash_tick():
    """A malformed response from one service must not lose the whole tick."""
    plugin = _plugin_with_tools_json()

    def side_effect(req, **_kwargs):
        if "localhost:1001/" in req.full_url:
            raise http.client.BadStatusLine("bad status line")
        return _ok_mock_response()

    with mock.patch.object(
        uptime_witness.urllib.request, "urlopen", side_effect=side_effect
    ):
        summary, details = plugin.produce()

    by_name = {d["service"]: d for d in details}
    assert "masala" in by_name
    assert by_name["masala"]["ok"] is False
    assert by_name["masala"]["status_code"] is None
    assert "BadStatusLine" in by_name["masala"]["error"]

    other_ok = [d for d in details if d["service"] != "masala" and d["ok"] is True]
    assert len(other_ok) == len(details) - 1
    assert summary == {"ok": len(details) - 1, "total": len(details)}


def test_invalid_port_recorded_not_ok():
    """A service with a non-positive-int port is skipped cleanly."""
    with tempfile.TemporaryDirectory() as tmp:
        tools_path = os.path.join(tmp, "tools.json")
        with open(tools_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "tools": [
                        {"name": "good", "port": 9000, "live": True},
                        {"name": "bad-string", "port": "9001", "live": True},
                        {"name": "bad-negative", "port": -1, "live": True},
                        {"name": "bad-missing", "live": True},
                    ]
                },
                f,
            )

        plugin = _plugin_with_tools_json(tools_path)
        with mock.patch.object(
            uptime_witness.urllib.request, "urlopen", return_value=_ok_mock_response()
        ):
            summary, details = plugin.produce()

    assert summary["total"] == 4
    assert summary["ok"] == 1

    good = next(d for d in details if d["service"] == "good")
    assert good["ok"] is True
    assert good["status_code"] == 200

    for name in ("bad-string", "bad-negative", "bad-missing"):
        bad = next(d for d in details if d["service"] == name)
        assert bad["ok"] is False
        assert bad["status_code"] is None
        assert bad["url"] is None
        assert "invalid port" in bad["error"]


@pytest.mark.parametrize(
    "make_bad,exc_name",
    [
        (lambda p: None, "FileNotFoundError"),
        (lambda p: open(p, "w").write("not json"), "JSONDecodeError"),
    ],
)
def test_unreadable_tools_json_logs_fallback_warning(make_bad, exc_name, capsys):
    """Falling back to the hardcoded list must be visible to operators."""
    with tempfile.TemporaryDirectory() as tmp:
        tools_path = os.path.join(tmp, "tools.json")
        make_bad(tools_path)
        plugin = _plugin_with_tools_json(tools_path)
        with mock.patch.object(
            uptime_witness.urllib.request, "urlopen", return_value=_ok_mock_response()
        ):
            plugin.produce()

    captured = capsys.readouterr()
    assert captured.err.startswith("WARNING:")
    assert "could not read" in captured.err
    assert tools_path in captured.err
    assert exc_name in captured.err
    assert "hardcoded fallback service list" in captured.err
