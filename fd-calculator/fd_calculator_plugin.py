"""Computes fixed deposit maturity amounts across a fixed cycling list of tenures, quarterly compounding."""

from harness.shitpost_base import Shitpost

PRINCIPAL = 50000.0
RATE = 0.07
N = 4
TENURES = [1, 2, 3, 5, 10]


class FdCalculatorPlugin(Shitpost):
    """Emit the maturity amount for one TENURES entry per tick, cycling through the list."""

    name = "fd-calculator"
    internal = False
    commit_template = "fd {tenure_years}y: {maturity_amount}"

    def produce(self) -> dict:
        state = self._load_persisted_state({"index": 0})
        index = state["index"]

        years = TENURES[index]
        maturity = PRINCIPAL * (1 + RATE / N) ** (N * years)

        result = {
            "tenure_years": years,
            "maturity_amount": round(maturity, 2),
        }

        self._save_persisted_state({"index": (index + 1) % len(TENURES)})

        return result
