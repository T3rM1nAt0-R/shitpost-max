import os
import sys
from pathlib import Path

_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT)
sys.path.insert(0, _PLUGIN_DIR)

from fortune_cookie_factory_plugin import FortuneCookieFactoryPlugin


def test_cycles_through_all_fortunes_in_order(tmp_path, monkeypatch):
    plugin = FortuneCookieFactoryPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    seen = []
    for _ in range(6):
        result = plugin.produce()
        seen.append(result["fortune"])

    assert seen == FortuneCookieFactoryPlugin._FORTUNES
