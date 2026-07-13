import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)
import random
from card_shuffler_plugin import DECK, fisher_yates_shuffle, overhand_shuffle, naive_swap_shuffle, shannon_entropy, CardShufflerPlugin

def test_deck_has_52_cards():
    assert len(DECK) == 52
    assert len(set(DECK)) == 52

def test_fisher_yates_known_value():
    result = fisher_yates_shuffle([0, 1, 2, 3, 4], random.Random(42))
    assert result == [3, 1, 2, 4, 0]

def test_overhand_returns_flat_deck_same_cards():
    rng = random.Random(1)
    result = overhand_shuffle(DECK, rng)
    assert len(result) == 52, f"expected 52 flat cards, got shape suggesting nesting: {len(result)}"
    assert set(result) == set(DECK)

def test_naive_swap_preserves_all_cards():
    rng = random.Random(1)
    result = naive_swap_shuffle(DECK, rng, 52)
    assert sorted(result) == sorted(DECK)

def test_shannon_entropy_known_values():
    assert shannon_entropy([]) == 0.0
    assert shannon_entropy(["a", "a", "a"]) == 0.0  # all same, zero entropy
    import math
    assert abs(shannon_entropy(["a", "b"]) - 1.0) < 1e-9  # 2 equally likely outcomes = 1 bit

def test_produce_runs(tmp_path, monkeypatch):
    p = CardShufflerPlugin()
    monkeypatch.setattr(p, "_plugin_dir", lambda: str(tmp_path))
    for _ in range(3):
        r = p.produce()
        assert len(r["deck_order"]) == 52

def test_forced_shuffle_algo_env_var(tmp_path, monkeypatch):
    monkeypatch.setenv("SHUFFLE_ALGO", "fisher_yates")
    p = CardShufflerPlugin()
    monkeypatch.setattr(p, "_plugin_dir", lambda: str(tmp_path))
    algos_seen = {p.produce()["algorithm"] for _ in range(5)}
    assert algos_seen == {"fisher_yates"}, f"SHUFFLE_ALGO not respected: {algos_seen}"

def test_naive_swaps_env_var(tmp_path, monkeypatch):
    monkeypatch.setenv("SHUFFLE_ALGO", "naive_swap")
    monkeypatch.setenv("NAIVE_SWAPS", "3")
    p = CardShufflerPlugin()
    monkeypatch.setattr(p, "_plugin_dir", lambda: str(tmp_path))
    p.produce()
    # can't directly observe swap count from output, but confirm it doesn't crash and preserves the deck
    r = p.produce()
    assert sorted(r["deck_order"]) == sorted(DECK)

def test_shuffle_stats_json_written(tmp_path, monkeypatch):
    p = CardShufflerPlugin()
    monkeypatch.setattr(p, "_plugin_dir", lambda: str(tmp_path))
    for _ in range(4):
        p.produce()
    import json as _json
    stats = _json.loads((tmp_path / "shuffle_stats.json").read_text())
    assert stats["total_shuffles"] == 4
    assert set(stats["avg_entropy_per_algorithm"].keys()) <= {"fisher_yates", "overhand", "naive_swap"}
