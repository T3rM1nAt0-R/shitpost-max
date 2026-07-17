import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from binary_heap_demo_plugin import BinaryHeapDemoPlugin

KNOWN_HEAPS = [
    [5], [3, 5], [3, 5, 8], [5, 8], [1, 8, 5], [5, 8], [8],
]
KNOWN_VALUES = [5, 3, 8, 3, 1, 1, 5]


def test_op_sequence_matches_known_values(tmp_path, monkeypatch):
    plugin = BinaryHeapDemoPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    heaps = []
    values = []
    for _ in range(7):
        result = plugin.produce()
        heaps.append(result["heap"])
        values.append(result["value"])

    assert heaps == KNOWN_HEAPS
    assert values == KNOWN_VALUES
