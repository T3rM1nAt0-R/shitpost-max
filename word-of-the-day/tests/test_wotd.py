import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)
from wotd_plugin import WordOfTheDayPlugin, WORDLIST

def test_wordlist_shape():
    assert len(WORDLIST) == 5
    for entry in WORDLIST:
        assert set(entry.keys()) == {"word", "definition", "part_of_speech"}

def test_falls_back_to_template_on_ollama_failure(tmp_path, monkeypatch):
    p = WordOfTheDayPlugin()
    monkeypatch.setattr(p, "_plugin_dir", lambda: str(tmp_path))
    monkeypatch.setattr(p, "_call_ollama", lambda prompt: (_ for _ in ()).throw(ConnectionError("down")))
    r = p.produce()
    assert r["source"] == "template"
    assert r["example"] == f"The {r['word']} was unexpected."

def test_uses_ollama_when_available(tmp_path, monkeypatch):
    p = WordOfTheDayPlugin()
    monkeypatch.setattr(p, "_plugin_dir", lambda: str(tmp_path))
    monkeypatch.setattr(p, "_call_ollama", lambda prompt: "  A real generated sentence.  ")
    r = p.produce()
    assert r["source"] == "ollama"
    assert r["example"] == "A real generated sentence."

def test_corrupt_state_handled(tmp_path, monkeypatch):
    p = WordOfTheDayPlugin()
    monkeypatch.setattr(p, "_plugin_dir", lambda: str(tmp_path))
    (tmp_path / "word_of_the_day_state.json").write_text("not json{{{")
    monkeypatch.setattr(p, "_call_ollama", lambda prompt: "x")
    r = p.produce()
    assert r["tick"] == 1
