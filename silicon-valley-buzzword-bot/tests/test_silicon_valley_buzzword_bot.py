import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from silicon_valley_buzzword_bot_plugin import SiliconValleyBuzzwordBotPlugin


def test_produce_terminates_and_resets_once_vocabulary_is_exhausted(tmp_path, monkeypatch):
    """Only 4x4x4=64 buzzwords are possible and buzzwords.txt never prunes
    old entries, so once all 64 have been seen the old code's uniqueness
    retry loop could never find a "new" one and spun forever (this pegged
    8 CPU cores in production on 2026-07-14 for 5+ hours). Pre-seed every
    possible combination so this test exercises exactly that exhausted
    state, and confirm produce() still returns promptly instead of
    hanging."""
    p = SiliconValleyBuzzwordBotPlugin()
    monkeypatch.setattr(p, "_plugin_dir", lambda: str(tmp_path))

    prefixes = ["Giga", "Hyper", "Inno", "Next"]
    roots = ["Wave", "Revolution", "Breakthrough", "Shift"]
    suffixes = ["Tech", "Venture", "Innovation", "Future"]
    all_combos = [
        f"{pre}{root}{suf}" for pre in prefixes for root in roots for suf in suffixes
    ]
    assert len(all_combos) == 64

    buzzwords_path = tmp_path / "buzzwords.txt"
    buzzwords_path.write_text(
        "".join(f"{word} — 2026-07-14T00:00:00+00:00\n" for word in all_combos)
    )

    result = p.produce()

    assert result["buzzword"] in all_combos
    # The exhausted history was reset (not left to grow toward exhaustion
    # again on the very next tick) -- confirms the plugin recovers into a
    # fresh cycle rather than merely surviving one exhausted tick.
    assert buzzwords_path.read_text().count("—") == 1


def test_produce_still_finds_a_unique_word_when_vocabulary_is_not_exhausted(tmp_path, monkeypatch):
    p = SiliconValleyBuzzwordBotPlugin()
    monkeypatch.setattr(p, "_plugin_dir", lambda: str(tmp_path))

    result = p.produce()
    assert "buzzword" in result
    assert (tmp_path / "buzzwords.txt").read_text().count("—") == 1
