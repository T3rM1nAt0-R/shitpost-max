"""Projects a retirement corpus growing via fixed monthly contribution and growth rate until it crosses a fixed target, then resets."""

from harness.shitpost_base import Shitpost

MONTHLY_CONTRIBUTION = 10000.0
ANNUAL_RATE = 0.10
MONTHLY_RATE = ANNUAL_RATE / 12
TARGET = 1000000.0


class RetirementSimPlugin(Shitpost):
    """Emit one month of retirement corpus growth per tick, resetting once TARGET is crossed."""

    name = "retirement-sim"
    internal = False
    commit_template = "retirement month {month}: corpus {corpus}"

    def produce(self) -> dict:
        state = self._load_persisted_state({"month": 0, "corpus": 0.0, "done": False})

        if state["done"]:
            state = {"month": 0, "corpus": 0.0, "done": False}

        month = state["month"] + 1
        corpus = state["corpus"] * (1 + MONTHLY_RATE) + MONTHLY_CONTRIBUTION
        target_reached = corpus >= TARGET

        result = {
            "month": month,
            "corpus": round(corpus, 2),
            "target_reached": target_reached,
        }

        self._save_persisted_state({"month": month, "corpus": corpus, "done": target_reached})

        return result
