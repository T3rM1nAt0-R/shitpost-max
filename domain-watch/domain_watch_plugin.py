import json
import os
import sys
from datetime import datetime, timezone
import socket
import urllib.error
import urllib.request
from urllib.parse import urlparse

from harness.shitpost_base import Shitpost


class DomainWatchPlugin(Shitpost):
    """Check whether a specific domain has dropped/become available."""

    name = "domain-watch"
    internal = False
    commit_template = "domain-watch: {domain} {status}"

    def __init__(self):
        super().__init__()

    def produce(self) -> dict:
        """Return the domain status and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state(default=self._default_state())

        domain = state["domain"]

        try:
            response = urllib.request.urlopen(
                f"https://rdap.org/domain/{domain}", timeout=10
            )
            rdap_data = json.loads(response.read().decode())

            expires = None
            status = "unknown"
            for entity in rdap_data.get("entities", []):
                if entity["roles"] and "admin" in entity["roles"]:
                    expires = entity.get("events", [{}])[0].get("date")
                    break

            if expires:
                expires = datetime.strptime(expires, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()
                status = "active" if expires > datetime.now(timezone.utc).timestamp() else "expired"
            else:
                status = "unknown"

        except (OSError, KeyError):
            try:
                whois_info = socket.gethostbyname(domain)
                status = "available" if whois_info == domain else "unknown"
            except socket.gaierror:
                status = "unknown"

        resolves = True if status != "unknown" else False

        state["status"] = status
        state["expires"] = expires
        state["resolves"] = resolves
        state["tick"] += 1

        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "domain": domain,
            "status": status,
            "expires": expires,
            "resolves": resolves,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _default_state() -> dict:
        return {
            "domain": os.getenv("DOMAIN", "example.com"),
            "status": "unknown",
            "expires": None,
            "resolves": False,
            "tick": 0,
        }
