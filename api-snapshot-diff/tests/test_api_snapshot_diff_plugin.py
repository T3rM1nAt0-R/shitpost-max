import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from api_snapshot_diff_plugin import ApiSnapshotDiffPlugin


def test_diff_matches_ground_truth():
    plugin = ApiSnapshotDiffPlugin()
    result = plugin.produce()
    assert result["added"] == []
    assert result["removed"] == ["region"]
    assert result["changed"] == ["users", "version"]
