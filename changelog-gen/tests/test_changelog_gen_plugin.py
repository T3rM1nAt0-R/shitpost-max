import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from changelog_gen_plugin import ChangelogGenPlugin

EXPECTED = [
    ("v1.2.0", {"feat": ["add dark mode"], "fix": ["login redirect loop"], "chore": ["bump deps"], "docs": [], "other": []}),
    ("v1.3.0", {"feat": ["export to CSV", "keyboard shortcuts"], "fix": ["crash on empty input"], "chore": [], "docs": [], "other": []}),
    ("v1.4.0", {"feat": [], "fix": ["timezone bug"], "chore": ["update readme"], "docs": ["fix typo"], "other": []}),
]


def test_full_cycle_matches_ground_truth(tmp_path, monkeypatch):
    plugin = ChangelogGenPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for expected_version, expected_grouped in EXPECTED:
        result = plugin.produce()
        assert result["version"] == expected_version
        assert result["grouped"] == expected_grouped


def test_wraps_around(tmp_path, monkeypatch):
    plugin = ChangelogGenPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    for _ in range(len(EXPECTED)):
        plugin.produce()
    result = plugin.produce()
    assert result["version"] == "v1.2.0"
