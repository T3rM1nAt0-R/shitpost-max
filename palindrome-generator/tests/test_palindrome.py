import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)
from palindrome import PalindromeGenerator

def test_is_valid_palindrome():
    p = PalindromeGenerator()
    assert p._is_valid_palindrome("A man a plan a canal Panama") is True
    assert p._is_valid_palindrome("racecar") is True
    assert p._is_valid_palindrome("hello world") is False
    assert p._is_valid_palindrome("") is False
    assert p._is_valid_palindrome("!!!") is False

def test_state_persists_across_ticks(tmp_path, monkeypatch):
    p = PalindromeGenerator()
    monkeypatch.setattr(p, "_plugin_dir", lambda: str(tmp_path))
    monkeypatch.setattr(p, "_call_ollama", lambda prompt: "racecar")
    r1 = p.produce()
    assert r1["tick"] == 1
    assert r1["accepted"] is True
    r2 = p.produce()
    assert r2["tick"] == 2, f"tick did not persist across calls: got {r2['tick']}"
    assert r2["target"] == 20, f"target did not persist: got {r2['target']}"
