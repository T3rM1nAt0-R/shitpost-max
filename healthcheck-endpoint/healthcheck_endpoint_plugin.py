import http.server
import json
import os
import socketserver
import time
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class HealthcheckPlugin(Shitpost):
    """HTTP server with a /health endpoint."""

    name = "healthcheck-endpoint"
    internal = False
    commit_template = "health: tick {tick} uptime {uptime}s requests {requests}"

    # Class-level state so the Handler inner class and static methods
    # can access them via HealthcheckPlugin._xxx.
    _uptime_start: float = 0.0
    _request_count: int = 0
    _tick: int = 0

    def __init__(self):
        super().__init__()
        HealthcheckPlugin._uptime_start = time.time()
        HealthcheckPlugin._request_count = 0
        HealthcheckPlugin._tick = 0

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/health':
                uptime = int(time.time() - HealthcheckPlugin._uptime_start)
                tick = HealthcheckPlugin._tick
                requests = HealthcheckPlugin._request_count
                response = {
                    "status": "ok",
                    "uptime": uptime,
                    "tick": tick,
                    "requests": requests,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            else:
                response = {
                    "error": "not found",
                    "path": self.path
                }
                self.send_error(404, json.dumps(response))

        def log_message(self, format, *args):
            pass

    @staticmethod
    def _increment_tick():
        HealthcheckPlugin._tick += 1

    def produce(self) -> dict:
        """Increment tick and return current health-check state."""
        self._increment_tick()
        HealthcheckPlugin._request_count += 1

        return {
            "tick": HealthcheckPlugin._tick,
            "uptime": int(time.time() - HealthcheckPlugin._uptime_start),
            "requests": HealthcheckPlugin._request_count,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
