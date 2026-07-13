import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)
from lru_cache import LRUCache
from lru_witness_plugin import LRUCacheWitnessPlugin

def test_lru_eviction_order():
    c = LRUCache(capacity=2)
    c.put(1, "a"); c.put(2, "b")
    assert c.get(1) == "a"  # 1 now most-recent
    c.put(3, "c")  # should evict 2 (least recently used), not 1
    assert c.get(2) is None
    assert c.get(1) == "a"
    assert c.get(3) == "c"

def test_lru_len():
    c = LRUCache(capacity=5)
    c.put(1, "x"); c.put(2, "y")
    assert len(c) == 2

def test_corrupt_state_file_handled(tmp_path, monkeypatch):
    p = LRUCacheWitnessPlugin()
    monkeypatch.setattr(p, "_plugin_dir", lambda: str(tmp_path))
    (tmp_path / "lru_cache_witness_state.json").write_text("not valid json{{{")
    result = p.produce()  # must not raise
    assert result["tick"] == 1

def test_produce_runs(tmp_path, monkeypatch):
    p = LRUCacheWitnessPlugin()
    monkeypatch.setattr(p, "_plugin_dir", lambda: str(tmp_path))
    r = p.produce()
    assert r["tick_hits"] + r["tick_misses"] == 1000
    assert r["cache_size"] <= 100
