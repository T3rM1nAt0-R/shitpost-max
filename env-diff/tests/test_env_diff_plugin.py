import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from env_diff_plugin import EnvDiffPlugin


def test_missing_and_extra_match_ground_truth():
    plugin = EnvDiffPlugin()
    result = plugin.produce()
    assert result["missing"] == ["API_KEY", "SECRET_KEY"]
    assert result["extra"] == ["REDIS_URL"]
