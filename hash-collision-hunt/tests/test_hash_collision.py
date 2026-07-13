import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)
from hash_collision_plugin import weak_hash, HashCollisionHuntPlugin

def test_weak_hash_known_values():
    assert weak_hash("hello") == 20
    assert weak_hash("AAAAAAAA") == 8

def test_corrupt_state_handled(tmp_path, monkeypatch):
    p = HashCollisionHuntPlugin()
    monkeypatch.setattr(p, "_plugin_dir", lambda: str(tmp_path))
    (tmp_path / "hash_collision_state.json").write_text("not json{{{")
    r = p.produce()
    assert r["tick"] == 1

def test_produce_runs_and_fills_table(tmp_path, monkeypatch):
    p = HashCollisionHuntPlugin()
    monkeypatch.setattr(p, "_plugin_dir", lambda: str(tmp_path))
    r = p.produce()
    assert r["total_hashes"] == 10000
    assert 0 <= r["fill_ratio"] <= 1
    r2 = p.produce()
    assert r2["total_hashes"] == 20000
    assert r2["fill_ratio"] >= r["fill_ratio"]  # table only grows
