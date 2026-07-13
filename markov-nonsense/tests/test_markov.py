import os, sys
from pathlib import Path
import random
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)
from markov_plugin import CORPUS, build_bigram_table, generate_sentence, MarkovNonsensePlugin

def test_bigram_table_known():
    table = build_bigram_table(CORPUS)
    assert len(table) == 16
    assert table[("the", "cat")] == {"sat": 1, "chased": 1}

def test_generate_sentence_ends_properly():
    table = build_bigram_table(CORPUS)
    rng = random.Random(42)
    sentence = generate_sentence(table, rng)
    words = sentence.split()
    assert len(words) <= 50
    assert words[-1][-1] in ".!?" or len(words) == 50

def test_produce_returns_full_sentence_not_one_word(tmp_path, monkeypatch):
    p = MarkovNonsensePlugin()
    monkeypatch.setattr(p, "_plugin_dir", lambda: str(tmp_path))
    r = p.produce()
    assert r["word_count"] >= 3, f"sentence looks truncated to one word: {r['sentence']!r}"
    assert len(r["sentence"].split()) == r["word_count"]
