"""Computes the future value of a fixed one-time investment across a fixed cycling list of holding periods."""

from harness.shitpost_base import Shitpost

PRINCIPAL = 100000.0
RATE = 0.10
YEARS = [0, 1, 5, 10, 20]


class LumpsumCalculatorPlugin(Shitpost):
    """Emit the future value for one YEARS entry per tick, cycling through the list."""

    name = "lumpsum-calculator"
    internal = False
    commit_template = "lumpsum {year}y: {future_value}"

    def produce(self) -> dict:
        state = self._load_persisted_state({"index": 0})
        index = state["index"]

        year = YEARS[index]
        fv = PRINCIPAL * (1 + RATE) ** year

        result = {
            "year": year,
            "future_value": round(fv, 2),
        }

        self._save_persisted_state({"index": (index + 1) % len(YEARS)})

        return result
