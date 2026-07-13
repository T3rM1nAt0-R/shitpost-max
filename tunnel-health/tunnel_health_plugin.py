#!/usr/bin/env python3

import os
import subprocess
from datetime import datetime, timezone
import requests

from harness.shitpost_base import Shitpost


class TunnelHealthPlugin(Shitpost):
    """Check Cloudflare tunnel health."""

    name = "tunnel-health"
    internal = True
    commit_template = "tunnel: service {service_active}, tunnel {tunnel_up}"

    def _persisted_state_path(self) -> str:
        """Use tunnel_state.json to preserve existing persisted state."""
        return os.path.join(self._plugin_dir(), "tunnel_state.json")

    def produce(self) -> dict | None:
        """Return the tunnel health state and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "service_active": False,
            "tunnel_up": False,
            "tick": 0,
        })

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

        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "service_active": state["service_active"],
            "tunnel_up": state["tunnel_up"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
