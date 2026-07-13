import os
import sys
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class HighIQCertifierPlugin(Shitpost):
    """Append 'still high IQ' to still-high-iq.txt per tick."""

    name = "high-iq-certifier"
    internal = False
    commit_template = "still high IQ"

    def produce(self) -> dict:
        """Return the next line and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        timestamp = datetime.now(timezone.utc).isoformat()

        with open(os.path.join(plugin_dir, "still-high-iq.txt"), "a", encoding="utf-8") as f:
            f.write(f"still high IQ — {timestamp}\n")

        return {
            "tick": 1,
            "timestamp": timestamp,
        }
