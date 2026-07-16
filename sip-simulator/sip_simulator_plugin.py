"""Simulates a Systematic Investment Plan over 36 months with a fixed repeating sequence of monthly returns, then resets."""

from harness.shitpost_base import Shitpost

MONTHLY_RETURNS = [0.01, 0.02, -0.01, 0.015, 0.005, -0.02, 0.03, 0.0, 0.01, -0.005, 0.02, 0.01]
CONTRIBUTION = 5000.0
CYCLE = 36


class SipSimulatorPlugin(Shitpost):
    """Emit one month of SIP growth per tick, cycling every CYCLE months."""

    name = "sip-simulator"
    internal = False
    commit_template = "sip month {month}: corpus {corpus}"

    def produce(self) -> dict:
        state = self._load_persisted_state({"month": 1, "corpus": 0.0, "invested": 0.0})
        month = state["month"]
        corpus = state["corpus"]
        invested = state["invested"]

        r = MONTHLY_RETURNS[(month - 1) % 12]
        corpus = corpus * (1 + r) + CONTRIBUTION
        invested += CONTRIBUTION

        result = {
            "month": month,
            "monthly_return": round(r, 4),
            "corpus": round(corpus, 2),
            "invested": round(invested, 2),
        }

        if month == CYCLE:
            self._save_persisted_state({"month": 1, "corpus": 0.0, "invested": 0.0})
        else:
            self._save_persisted_state({"month": month + 1, "corpus": corpus, "invested": invested})

        return result
