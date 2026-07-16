"""Emits a fixed loan's monthly amortization schedule row by row, forever, until it's paid off and does it again."""

from harness.shitpost_base import Shitpost

PRINCIPAL = 120000.0
ANNUAL_RATE = 0.09
TENURE_MONTHS = 12
MONTHLY_RATE = ANNUAL_RATE / 12
PAYMENT = PRINCIPAL * MONTHLY_RATE * (1 + MONTHLY_RATE) ** TENURE_MONTHS / (
    (1 + MONTHLY_RATE) ** TENURE_MONTHS - 1
)


class LoanAmortizationPlugin(Shitpost):
    """Emit one amortization row per tick, cycling every TENURE_MONTHS."""

    name = "loan-amortization"
    internal = False
    commit_template = "loan month {month}: paid {payment}, balance {balance}"

    def produce(self) -> dict:
        state = self._load_persisted_state({"month": 1, "balance": PRINCIPAL})
        month = state["month"]
        balance = state["balance"]

        interest = balance * MONTHLY_RATE
        principal_paid = PAYMENT - interest
        new_balance = max(balance - principal_paid, 0.0)

        result = {
            "month": month,
            "payment": round(PAYMENT, 2),
            "interest": round(interest, 2),
            "principal_paid": round(principal_paid, 2),
            "balance": round(new_balance, 2),
        }

        if month == TENURE_MONTHS:
            self._save_persisted_state({"month": 1, "balance": PRINCIPAL})
        else:
            self._save_persisted_state({"month": month + 1, "balance": new_balance})

        return result
