import json
import os
import gzip
import bz2

from harness.shitpost_base import Shitpost


class CompressionLabPlugin(Shitpost):
    """Compress sibling logs and track compression ratios."""

    name = "compression-lab"
    internal = False
    commit_template = "compression-lab: {sibling_count} logs, {raw_bytes}B → gzip={gzip[compressed_bytes]}B ({gzip[ratio]:.2f}x), bzip2={bzip2[compressed_bytes]}B ({bzip2[ratio]:.2f}x)"

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

        state = self._load_persisted_state({
            "tick": 0,
            "sibling_count": 0,
            "raw_bytes": 0,
            "algorithms": {
                "gzip": {"compressed_bytes": 0, "ratio": 1.0},
                "bzip2": {"compressed_bytes": 0, "ratio": 1.0}
            }
        })
        sibling_count = 0
        raw_bytes = 0

        content_chunks: list[bytes] = []
        for sibling in os.listdir(".."):
            sibling_path = os.path.join("..", sibling)
            if os.path.isdir(sibling_path) and "state.jsonl" in os.listdir(sibling_path):
                sibling_count += 1
                with open(os.path.join(sibling_path, "state.jsonl"), "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            log = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        encoded = json.dumps(log).encode("utf-8")
                        raw_bytes += len(encoded)
                        content_chunks.append(encoded)

        if sibling_count == 0:
            state["raw_bytes"] = 0
        else:
            data = b"\n".join(content_chunks)
            ratios = self._compress_data(data)
            state["algorithms"] = ratios

        state["tick"] += 1

        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "sibling_count": sibling_count,
            "raw_bytes": raw_bytes,
            **state["algorithms"]
        }
