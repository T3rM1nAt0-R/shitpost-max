import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

import json
from unittest.mock import patch, MagicMock

from system_prompt_tester_plugin import SystemPromptTesterPlugin, SYSTEM_PROMPTS, USER_MESSAGE


def test_messages_payload_built_correctly(tmp_path, monkeypatch):
    plugin = SystemPromptTesterPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))

    captured = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps({"message": {"role": "assistant", "content": "pizza"}}).encode()

    def fake_urlopen(req, *a, **k):
        captured.append(json.loads(req.data))
        return FakeResponse()

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        for expected_prompt in SYSTEM_PROMPTS:
            result = plugin.produce()
            assert result["system_prompt"] == expected_prompt
            assert result["output"] == "pizza"

    for i, payload in enumerate(captured):
        assert payload["messages"][0] == {"role": "system", "content": SYSTEM_PROMPTS[i]}
        assert payload["messages"][1] == {"role": "user", "content": USER_MESSAGE}


def test_produce_returns_none_on_failure(tmp_path, monkeypatch):
    plugin = SystemPromptTesterPlugin()
    monkeypatch.setattr(plugin, "_plugin_dir", lambda: str(tmp_path))
    with patch("urllib.request.urlopen", side_effect=OSError("down")):
        assert plugin.produce() is None
