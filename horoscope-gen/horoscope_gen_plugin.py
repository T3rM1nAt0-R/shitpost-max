"""AI-powered celestial determinism platform for personalized astrological content generation. Every horoscope is a cosmic growth opportunity."""

import os
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost


class HoroscopeGenPlugin(Shitpost):
    """Emit one daily horoscope message per tick, cycling through the 12 zodiac signs."""

    name = "horoscope-gen"
    internal = False
    commit_template = "{sign}: {message}"

    _SIGNS = [
        ("Aries", "A merge conflict today reveals your true leadership potential."),
        ("Taurus", "Resist the urge to refactor everything at once."),
        ("Gemini", "Two branches diverge; choose the one with fewer conflicts."),
        ("Cancer", "Your instincts about that flaky test are correct."),
        ("Leo", "Today, your pull request deserves the spotlight it demands."),
        ("Virgo", "A perfectly formatted commit message awaits your attention."),
        ("Libra", "Balance is key: one more dependency could tip the scales."),
        ("Scorpio", "That deprecated function you've been avoiding? Face it today."),
        ("Sagittarius", "An adventurous refactor calls, but check the tests first."),
        ("Capricorn", "Slow, steady progress on that backlog pays off this week."),
        ("Aquarius", "An unconventional architecture choice proves surprisingly wise."),
        ("Pisces", "Trust your gut about that race condition — it's real."),
    ]

    def produce(self) -> dict:
        """Emit the next zodiac sign's horoscope and update persistent files."""
        plugin_dir = self._plugin_dir()
        os.makedirs(plugin_dir, exist_ok=True)

        state = self._load_persisted_state({
            "sign_index": 0,
            "tick": 0,
        })

        sign, message = self._SIGNS[state["sign_index"] % len(self._SIGNS)]

        state["sign_index"] = (state["sign_index"] + 1) % len(self._SIGNS)
        state["tick"] += 1
        self._save_persisted_state(state)

        return {
            "tick": state["tick"],
            "sign": sign,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
