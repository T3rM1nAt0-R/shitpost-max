"""Computes the Equated Monthly Installment across a fixed cycling list of loan scenarios."""

from harness.shitpost_base import Shitpost

SCENARIOS = [
    (200000, 0.09, 24),
    (500000, 0.085, 60),
    (1000000, 0.075, 120),
    (50000, 0.12, 12),
    (300000, 0.10, 36),
]


def _emi(principal, annual_rate, tenure_months):
    r = annual_rate / 12
    return principal * r * (1 + r) ** tenure_months / ((1 + r) ** tenure_months - 1)


class EmiCalculatorPlugin(Shitpost):
    """Emit the EMI for one SCENARIOS entry per tick, cycling through the list."""

    name = "emi-calculator"
    internal = False
    commit_template = "emi {principal}@{annual_rate}: {emi}/mo"

    def produce(self) -> dict:
        state = self._load_persisted_state({"index": 0})
        index = state["index"]

        principal, annual_rate, tenure_months = SCENARIOS[index]
        emi_value = _emi(principal, annual_rate, tenure_months)

        result = {
            "principal": principal,
            "annual_rate": annual_rate,
            "tenure_months": tenure_months,
            "emi": round(emi_value, 2),
        }

        self._save_persisted_state({"index": (index + 1) % len(SCENARIOS)})

        return result
