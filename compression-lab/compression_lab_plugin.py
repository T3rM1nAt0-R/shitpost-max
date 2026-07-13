import json
import os
import sys
from datetime import datetime, timezone
import gzip
import bz2

from harness.shitpost_base import Shitpost


class CompressionLabPlugin(Shitpost):
    """Compress sibling logs and track compression ratios."""

    name = "compression-lab"
    internal = False
    commit_template = "compression-lab: {sibling_count} logs, {raw_bytes}B → gzip={gzip[compressed_bytes]}B ({gzip[ratio]:.2f}x), bzip2={bzip2[compressed_bytes]}B ({bzip2[ratio]:.2f}x)"

    def __init__(self):
        super().__init__()
        self._state_file_name = "compression_lab_state.json"

    def _load_state(self, plugin_dir: str) -> dict:
        """Load the running state, or initialise it."""
        path = os.path.join(plugin_dir, self._state_file_name)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    state = json.load(f)
            except json.JSONDecodeError as exc:
                print(
                    f"warning: compression-lab state file is corrupt ({exc}); starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            # Guard against manual tampering / old versions.
            required = {"tick", "sibling_count", "raw_bytes", "algorithms"}
            if not required.issubset(state.keys()):
                print(
                    "warning: compression-lab state missing keys; starting fresh",
                    file=sys.stderr,
                )
                return self._default_state()
            return state

        return self._default_state()

    @staticmethod
    def _default_state() -> dict:
        return {
            "tick": 0,
            "sibling_count": 0,
            "raw_bytes": 0,
            "algorithms": {
                "gzip": {"compressed_bytes": 0, "ratio": 1.0},
                "bzip2": {"compressed_bytes": 0, "ratio": 1.0}
            }
        }

    def _save_state(self, plugin_dir: str, state: dict) -> None:
        path = os.path.join(plugin_dir, self._state_file_name)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"), sort_keys=True)
            f.write("\n")
        os.replace(tmp_path, path)

    def _compress_data(self, data: bytes) -> dict:
        """Compress data with gzip and bzip2."""
        return {
            "gzip": {"compressed_bytes": len(gzip.compress(data)), "ratio": len(gzip.compress(data)) / len(data)},
            "bzip2": {"compressed_bytes": len(bz2.compress(data)), "ratio": len(bz2.compress(data)) / len(data)}
        }

    def produce(self) -> dict:
        """Scan siblings, compress logs, and log ratios."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_state(plugin_dir)
        sibling_count = 0
        raw_bytes = 0

        for sibling in os.listdir(".."):
            sibling_path = os.path.join("..", sibling)
            if os.path.isdir(sibling_path) and "state.jsonl" in os.listdir(sibling_path):
                sibling_count += 1
                with open(os.path.join(sibling_path, "state.jsonl"), "r", encoding="utf-8") as f:
                    for line in f:
                        log = json.loads(line)
                        raw_bytes += len(json.dumps(log).encode("utf-8"))

        if sibling_count == 0:
            state["raw_bytes"] = 0
        else:
            data = bytes(raw_bytes)
            ratios = self._compress_data(data)
            state.update(ratios)

        state["tick"] += 1

        self._save_state(plugin_dir, state)

        return {
            "tick": state["tick"],
            "sibling_count": sibling_count,
            "raw_bytes": raw_bytes,
            **state["algorithms"]
        }
