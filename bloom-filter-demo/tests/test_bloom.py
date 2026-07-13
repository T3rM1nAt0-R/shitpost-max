import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)
from bloom import BloomFilterDemo

def test_bit_positions_known():
    p = BloomFilterDemo()
    assert p._bit_positions("hello") == [216, 10, 225]

def test_add_and_might_contain_no_false_negative():
    p = BloomFilterDemo()
    bits = [0] * 1000
    p._add(bits, "hello")
    assert p._might_contain(bits, "hello") is True

def test_produce_runs_without_crash(tmp_path, monkeypatch):
    p = BloomFilterDemo()
    monkeypatch.setattr(p, "_plugin_dir", lambda: str(tmp_path))
    for _ in range(3):
        result = p.produce()
        assert result["bits_set"] <= 1000
        assert 0 <= result["fp_rate"] <= 1
