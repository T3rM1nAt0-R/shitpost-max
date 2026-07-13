import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)
from name_gen_plugin import SEEDS, build_ngram_table, NameGeneratorPlugin

def test_ngram_table_known():
    table = build_ngram_table(SEEDS, order=2)
    assert len(table) == 17
    assert table["an"] == {"n": 1, "\n": 1}

def test_corrupt_state_handled(tmp_path, monkeypatch):
    p = NameGeneratorPlugin()
    monkeypatch.setattr(p, "_plugin_dir", lambda: str(tmp_path))
    (tmp_path / "name_generator_state.json").write_text("not json{{{")
    r = p.produce()
    assert r["tick"] == 1

def test_produce_runs_and_dedups(tmp_path, monkeypatch):
    p = NameGeneratorPlugin()
    monkeypatch.setattr(p, "_plugin_dir", lambda: str(tmp_path))
    names = [p.produce()["name"] for _ in range(10)]
    assert all(len(n) <= 12 for n in names)

def test_env_vars_wired_through(tmp_path, monkeypatch):
    monkeypatch.setenv("MAX_NAME_LENGTH", "5")
    p = NameGeneratorPlugin()
    monkeypatch.setattr(p, "_plugin_dir", lambda: str(tmp_path))
    names = [p.produce()["name"] for _ in range(10)]
    assert all(len(n.split("_")[0]) <= 5 for n in names), f"MAX_NAME_LENGTH=5 not respected: {names}"
