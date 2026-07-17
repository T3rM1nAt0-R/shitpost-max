"""Computes the current moon phase, illumination, and age from pure astronomy math. No network dependency."""

import math
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost

SYNODIC_MONTH_DAYS = 29.530588853
REFERENCE_NEW_MOON = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)

PHASE_NAMES = [
    "New Moon",
    "Waxing Crescent",
    "First Quarter",
    "Waxing Gibbous",
    "Full Moon",
    "Waning Gibbous",
    "Last Quarter",
    "Waning Crescent",
]


def _compute(now):
    days_since = (now - REFERENCE_NEW_MOON).total_seconds() / 86400
    age = days_since % SYNODIC_MONTH_DAYS
    phase_fraction = age / SYNODIC_MONTH_DAYS
    illumination = (1 - math.cos(2 * math.pi * phase_fraction)) / 2 * 100
    idx = int((phase_fraction * 8) % 8)
    return {
        "age_days": round(age, 2),
        "illumination_pct": round(illumination, 1),
        "phase_name": PHASE_NAMES[idx],
    }


class MoonPhasePlugin(Shitpost):
    """Emit the current moon phase every tick (stateless, pure function of wall-clock time)."""

    name = "moon-phase"
    internal = False
    commit_template = "moon: {phase_name} ({illumination_pct}% lit)"

    def produce(self):
        return _compute(datetime.now(timezone.utc))
