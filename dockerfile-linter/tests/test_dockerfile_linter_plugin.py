import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from dockerfile_linter_plugin import DockerfileLinterPlugin


def test_good_dockerfile_has_no_issues(tmp_path, monkeypatch):
    plugin = DockerfileLinterPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    result = plugin.produce()
    assert result["filename"] == "good.Dockerfile"
    assert result["issue_count"] == 0


def test_bad_dockerfile_has_four_issues_then_wraps(tmp_path, monkeypatch):
    plugin = DockerfileLinterPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    plugin.produce()
    result = plugin.produce()
    assert result["filename"] == "bad.Dockerfile"
    assert result["issue_count"] == 4

    next_result = plugin.produce()
    assert next_result["filename"] == "good.Dockerfile"
