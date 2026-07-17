"""Shows a fixed progressive tax bracket table and the marginal-bracket liability for a fixed cycling list of incomes."""

from harness.shitpost_base import Shitpost

BRACKETS = [
    (0, 300000, 0.0),
    (300000, 700000, 0.05),
    (700000, 1000000, 0.10),
    (1000000, 1200000, 0.15),
    (1200000, 1500000, 0.20),
    (1500000, None, 0.30),
]
INCOMES = [250000, 500000, 900000, 1100000, 1400000, 2000000]


def _tax_liability(income):
    total = 0.0
    marginal_rate = 0.0
    for lo, hi, rate in BRACKETS:
        if income > lo:
            upper = income if hi is None else min(income, hi)
            total += (upper - lo) * rate
            marginal_rate = rate
        else:
            break
    return total, marginal_rate


class TaxBracketViewerPlugin(Shitpost):
    """Emit tax liability for one INCOMES entry per tick, cycling through the list."""

    name = "tax-bracket-viewer"
    internal = False
    commit_template = "tax income {income}: liability {liability}"

    def produce(self) -> dict:
        state = self._load_persisted_state({"index": 0})
        index = state["index"]

        income = INCOMES[index]
        liability, marginal_rate = _tax_liability(income)

        result = {
            "income": income,
            "liability": round(liability, 2),
            "marginal_rate": marginal_rate,
        }

        self._save_persisted_state({"index": (index + 1) % len(INCOMES)})

        return result
