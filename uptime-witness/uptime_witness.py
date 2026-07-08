"""Uptime witness plugin: silently health-check every live Atlas service.

Reads ``/opt/data/tools/deploy/tools.json`` (or the path in ``TOOLS_JSON``) to
discover services, then hits ``http://localhost:<port>/health`` from the host
loopback.  Each tick returns the multi-line ``(summary, details)`` form so the
harness writes one JSONL line per service plus a summary JSON file.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any

from harness.shitpost_base import Shitpost


# Fallback service list kept in sync with the real tools.json as a resilience
# measure in case that file is unreadable at tick time.
_FALLBACK_SERVICES: list[dict[str, Any]] = [
    {"name": "masala", "port": 1001, "live": True},
    {"name": "brief", "port": 1002, "live": True},
    {"name": "mood", "port": 1003, "live": True},
    {"name": "decisions", "port": 1004, "live": True},
    {"name": "links", "port": 1005, "live": True},
    {"name": "upload", "port": 1006, "live": True},
    {"name": "relay", "port": 1007, "live": True},
    {"name": "gamepad", "port": 1008, "live": True},
    {"name": "gitcrawl", "port": 1009, "live": True},
    {"name": "superhermes", "port": 1010, "live": True},
    {"name": "repo-analyzer", "port": 1011, "live": True},
    {"name": "testenv", "port": 1012, "live": True},
    {"name": "eval-loop-dashboard", "port": 1013, "live": True},
    {"name": "atlas-ops-console", "port": 1014, "live": True},
    {"name": "lifeos-shell", "port": 1015, "live": True},
    {"name": "postgres", "port": 1500, "live": True},
    {"name": "redis", "port": 1501, "live": True},
    {"name": "ollama", "port": 1601, "live": True},
    {"name": "filebrowser", "port": 1701, "live": True},
    {"name": "uptime-kuma", "port": 1801, "live": True},
]

# Short loopback-only timeout.  A service that cannot answer within this window
# is treated as down for this tick.
_HEALTH_TIMEOUT_SECONDS = 3.0


class UptimeWitnessPlugin(Shitpost):
    """Health-check logger for the Atlas homelab."""

    name = "uptime-witness"
    internal = True
    commit_template = "uptime: {ok}/{total} OK"

    def __init__(self, tools_json_path: str | None = None):
        super().__init__()
        self._tools_json_path = tools_json_path or os.environ.get(
            "TOOLS_JSON", "/opt/data/tools/deploy/tools.json"
        )

    def _discover_services(self) -> list[dict[str, Any]]:
        """Return live services from tools.json, or the hardcoded fallback."""
        try:
            with open(self._tools_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            print(
                f"WARNING: could not read {self._tools_json_path} "
                f"({type(exc).__name__}: {exc}); using hardcoded fallback service list",
                file=sys.stderr,
            )
            return [s for s in _FALLBACK_SERVICES if s.get("live")]

        tools = data.get("tools", []) if isinstance(data, dict) else []
        return [tool for tool in tools if isinstance(tool, dict) and tool.get("live")]

    @staticmethod
    def _check_service(service: dict[str, Any]) -> dict[str, Any]:
        """Hit one service's /health endpoint and return a detail dict."""
        name = service.get("name", "unknown")
        port = service.get("port")

        detail: dict[str, Any] = {
            "service": name,
            "port": port,
        }

        if not isinstance(port, int) or port <= 0:
            detail["url"] = None
            detail["status_code"] = None
            detail["response_ms"] = None
            detail["ok"] = False
            detail["error"] = f"invalid port: {port!r}"
            return detail

        url = f"http://localhost:{port}/health"
        detail["url"] = url

        start = time.perf_counter()
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=_HEALTH_TIMEOUT_SECONDS) as resp:
                _ = resp.read()
                status = resp.getcode()
        except urllib.error.HTTPError as exc:
            status = exc.code
        except urllib.error.URLError:
            status = None
        except TimeoutError:
            status = None
        except OSError:
            status = None
        except Exception as exc:
            status = None
            detail["error"] = f"{type(exc).__name__}: {exc}"

        elapsed_ms = int((time.perf_counter() - start) * 1000)

        detail["status_code"] = status
        detail["response_ms"] = elapsed_ms
        detail["ok"] = status == 200
        return detail

    def produce(self) -> tuple[dict, list[dict]]:
        """Check every live service and return the harness multi-line form."""
        services = self._discover_services()
        details = [self._check_service(svc) for svc in services]

        ok_count = sum(1 for d in details if d.get("ok"))
        summary = {
            "ok": ok_count,
            "total": len(details),
        }

        return summary, details
