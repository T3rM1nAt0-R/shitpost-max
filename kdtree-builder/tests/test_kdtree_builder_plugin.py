import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from kdtree_builder_plugin import KdtreeBuilderPlugin

KNOWN_NODE_COUNTS = [1, 2, 3, 4, 5, 6, 7]
KNOWN_DEPTHS = [1, 2, 3, 3, 4, 4, 4]


def test_insertion_stats_match_known_values(tmp_path, monkeypatch):
    plugin = KdtreeBuilderPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    node_counts = []
    depths = []
    for _ in range(7):
        result = plugin.produce()
        node_counts.append(result["node_count"])
        depths.append(result["depth"])

    assert node_counts == KNOWN_NODE_COUNTS
    assert depths == KNOWN_DEPTHS
