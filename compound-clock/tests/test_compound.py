import os, sys
from decimal import Decimal
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)
from compound_clock_plugin import CompoundClockPlugin

def test_known_values():
    cv = CompoundClockPlugin.compound_value
    assert cv(Decimal("1000"), Decimal("0.05"), 0) == Decimal("1000")
    assert cv(Decimal("1000"), Decimal("0.05"), 1) == Decimal("1000.136986301369863013698630")
    assert cv(Decimal("1000"), Decimal("0.05"), 4) == Decimal("1000.548057807242709152302778")

def test_corrupt_state_handled(tmp_path, monkeypatch):
    p = CompoundClockPlugin()
    monkeypatch.setattr(p, "_plugin_dir", lambda: str(tmp_path))
    (tmp_path / "compound_clock_state.json").write_text("not json{{{")
    r = p.produce()
    assert r["tick"] == 1

def test_day_caps_at_max_days(tmp_path, monkeypatch):
    monkeypatch.setenv("MAX_DAYS", "3")
    p = CompoundClockPlugin()
    monkeypatch.setattr(p, "_plugin_dir", lambda: str(tmp_path))
    days_seen = [p.produce()["day"] for _ in range(8)]
    assert days_seen == [0, 1, 2, 3, 3, 3, 3, 3], f"day did not cap correctly: {days_seen}"
