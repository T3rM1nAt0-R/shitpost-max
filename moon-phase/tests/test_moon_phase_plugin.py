import os, sys
from pathlib import Path
_PLUGIN_DIR = str(Path(__file__).resolve().parent.parent)
_REPO_ROOT = os.path.dirname(_PLUGIN_DIR)
sys.path.insert(0, _REPO_ROOT); sys.path.insert(0, _PLUGIN_DIR)

from datetime import datetime, timedelta, timezone

from moon_phase_plugin import _compute, REFERENCE_NEW_MOON, SYNODIC_MONTH_DAYS


def test_new_moon_at_reference_epoch():
    result = _compute(REFERENCE_NEW_MOON)
    assert result["age_days"] == 0.0
    assert result["illumination_pct"] == 0.0
    assert result["phase_name"] == "New Moon"


def test_full_moon_at_half_synodic_month():
    instant = REFERENCE_NEW_MOON + timedelta(days=SYNODIC_MONTH_DAYS / 2)
    result = _compute(instant)
    assert result["age_days"] == 14.77
    assert result["illumination_pct"] == 100.0
    assert result["phase_name"] == "Full Moon"


def test_age_always_in_valid_range():
    for days in range(0, 60):
        instant = REFERENCE_NEW_MOON + timedelta(days=days)
        result = _compute(instant)
        assert 0 <= result["age_days"] < SYNODIC_MONTH_DAYS
