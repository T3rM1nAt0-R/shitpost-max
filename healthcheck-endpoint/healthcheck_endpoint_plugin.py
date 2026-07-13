import http.server
import socketserver
import time
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class HealthcheckPlugin(Shitpost):
    """HTTP server with a /health endpoint."""

    name = "healthcheck-endpoint"
    internal = False
    commit_template = "health: tick {t} uptime {u}s requests {r}"

    def __init__(self):
        super().__init__()
        self._uptime_start = time.time()
        self._request_count = 0
        self._tick = 0

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
        """Start the HTTP server and handle requests."""
        self._increment_tick()
        PORT = int(os.getenv('PORT', '8888'))
        HOST = os.getenv('HOST', '127.0.0.1')

        with socketserver.TCPServer((HOST, PORT), HealthcheckPlugin.Handler) as httpd:
            try:
                while True:
                    time.sleep(1)
                    self._request_count += 1
            except KeyboardInterrupt:
                pass

        return {
            "tick": HealthcheckPlugin._tick,
            "uptime": int(time.time() - self._uptime_start),
            "requests": self._request_count,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
