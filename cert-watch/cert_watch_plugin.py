import json
import os
import socket
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from harness.shitpost_base import Shitpost
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from OpenSSL import SSL, crypto


# Fallback subdomain list kept in sync with the real tools.json as a resilience
# measure in case that file is unreadable at tick time.
_FALLBACK_SUBDOMAINS: list[dict[str, Any]] = [
    {"subdomain": "masala.i7.ovh"},
    {"subdomain": "brief.i7.ovh"},
    {"subdomain": "mood.i7.ovh"},
    {"subdomain": "decisions.i7.ovh"},
    {"subdomain": "links.i7.ovh"},
    {"subdomain": "upload.i7.ovh"},
    {"subdomain": "relay.i7.ovh"},
    {"subdomain": "gamepad.i7.ovh"},
    {"subdomain": "gitcrawl.i7.ovh"},
    {"subdomain": "superhermes.i7.ovh"},
    {"subdomain": "repo-analyzer.i7.ovh"},
    {"subdomain": "testenv.i7.ovh"},
    {"subdomain": "eval-loop-dashboard.i7.ovh"},
    {"subdomain": "atlas-ops-console.i7.ovh"},
    {"subdomain": "lifeos-shell.i7.ovh"},
]


class CertWatchPlugin(Shitpost):
    """TLS expiry logger for Atlas subdomains."""

    name = "cert-watch"
    internal = True
    commit_template = "cert: {min_days} days until nearest expiry"

    def __init__(self):
        super().__init__()
        self._state_file_name = "cert_summary.json"
        self._log_file_name = "cert_log.jsonl"
        self._tools_json_path = os.getenv("TOOLS_JSON", "/opt/data/tools/deploy/tools.json")
        self._warn_days = int(os.getenv("WARN_DAYS", 30))

    def _load_state(self, plugin_dir: str) -> Dict[str, Dict[str, int]]:
        """Load the running certificate state."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: cert summary file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return {}
        else:
            state = {}

        return state

    def _save_state(self, plugin_dir: str, state: Dict[str, Dict[str, int]]) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _append_log(self, plugin_dir: str, log_entry: Dict[str, str]) -> None:
        path = os.path.join(plugin_dir, self._log_file_name)
        with open(path, "a", encoding="utf-8") as f:
            json.dump(log_entry, f)
            f.write("\n")

    def _parse_certificate(self, domain: str) -> Tuple[int, datetime]:
        """Parse the TLS certificate for a given domain."""
        context = SSL.Context(SSL.TLSv1_2_METHOD)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn = SSL.Connection(context, sock)
        conn.set_connect_state()
        conn.connect((domain, 443))
        conn.do_handshake()

        cert_pem = conn.get_peer_certificate().to_cryptography_cert()
        cert = x509.load_pem_x509_certificate(cert_pem.public_bytes(serialization.Encoding.PEM), default_backend())
        not_after = cert.not_valid_after
        days_remaining = (not_after - datetime.now(timezone.utc)).days

        return days_remaining, not_after

    def _discover_subdomains(self) -> list[str]:
        """Return subdomains from tools.json, or the hardcoded fallback."""
        try:
            with open(self._tools_json_path, "r", encoding="utf-8") as f:
                tools_data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            print(
                f"WARNING: could not read {self._tools_json_path} "
                f"({type(exc).__name__}: {exc}); using hardcoded fallback subdomain list",
                file=sys.stderr,
            )
            return [t["subdomain"] for t in _FALLBACK_SUBDOMAINS if "subdomain" in t]

        return [tool["subdomain"] for tool in tools_data if "subdomain" in tool]

    def produce(self) -> Dict[str, str]:
        """Return the nearest certificate expiry and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        log_entries = []

        subdomains = self._discover_subdomains()

        min_days = float('inf')
        for subdomain in subdomains:
            days_remaining, not_after = self._parse_certificate(subdomain)
            state[subdomain] = {"expiry_date": not_after.isoformat(), "days_remaining": days_remaining}
            log_entries.append({"subdomain": subdomain, "expiry_date": not_after.isoformat(), "days_remaining": days_remaining})
            min_days = min(min_days, days_remaining)

        self._save_state(plugin_dir, state)
        for entry in log_entries:
            self._append_log(plugin_dir, entry)

        return {
            "min_days": min_days,
            "log_entries": log_entries,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
