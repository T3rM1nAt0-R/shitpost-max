#!/usr/bin/env python3

import json
import os
import sys
from datetime import datetime, timezone
import requests

from harness.shitpost_base import Shitpost


class TunnelHealthPlugin(Shitpost):
    """Check Cloudflare tunnel health."""

    name = "tunnel-health"
    internal = True
    commit_template = "tunnel: service {service_active}, tunnel {tunnel_up}"

    def __init__(self):
        super().__init__()
        self._state_file_name = "tunnel_state.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: tunnel state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"service_active", "tunnel_up", "tick"}
            if not required.issubset(state.keys()):
                print(
                    "warning: tunnel state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "service_active": False,
            "tunnel_up": False,
            "tick": 0,
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def produce(self) -> dict | None:
        """Return the tunnel health state and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)

        # Check if cloudflared service is active
        try:
            service_active = subprocess.run(["systemctl", "is-active", "cloudflared"], check=True, stdout=subprocess.PIPE).stdout.decode().strip() == 'active'
        except subprocess.CalledProcessError:
            service_active = False

        tunnel_up = False
        if service_active:
            # Fetch metrics and parse for cloudflared_tunnel_up gauge
            try:
                response = requests.get(os.getenv("METRICS_URL", "http://localhost:45678/metrics"))
                response.raise_for_status()
                metrics = response.text.split('\n')
                tunnel_up = any('cloudflared_tunnel_up 1' in line for line in metrics)
            except (requests.RequestException, ValueError):
                pass

        state["service_active"] = service_active
        state["tunnel_up"] = tunnel_up
        state["tick"] += 1

        self._save_state(plugin_dir, state)

        return {
            "tick": state["tick"],
            "service_active": state["service_active"],
            "tunnel_up": state["tunnel_up"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
