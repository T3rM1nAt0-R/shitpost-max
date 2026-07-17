import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from pirate_translator_plugin import PirateTranslatorPlugin

KNOWN_TRANSLATIONS = [
    "Ahoy me matey",
    "Be th' treasure here",
    "Ye are me matey",
    "Aye, ahoy there",
    "Th' map be real",
]


def test_translations_match_known_values(tmp_path, monkeypatch):
    plugin = PirateTranslatorPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen = []
    for _ in range(5):
        result = plugin.produce()
        seen.append(result["translated"])

    assert seen == KNOWN_TRANSLATIONS
