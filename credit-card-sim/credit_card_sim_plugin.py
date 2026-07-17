"""Simulates a credit card balance for 24 months of minimum payments, demonstrating the debt trap, then resets."""

from harness.shitpost_base import Shitpost

START_BALANCE = 5000.0
APR = 0.24
MONTHLY_RATE = APR / 12
MONTHLY_PURCHASE = 200.0
CYCLE_LENGTH = 24


class CreditCardSimPlugin(Shitpost):
    """Emit one month of credit card balance simulation per tick, cycling every CYCLE_LENGTH months."""

    name = "credit-card-sim"
    internal = False
    commit_template = "cc month {cycle_month}: balance {balance_end}"

    def produce(self) -> dict:
        state = self._load_persisted_state({"cycle_month": 1, "balance": START_BALANCE})
        cycle_month = state["cycle_month"]
        balance = state["balance"]

        interest = balance * MONTHLY_RATE
        min_payment = max(25.0, 0.02 * balance)
        new_balance = balance + interest + MONTHLY_PURCHASE - min_payment

        result = {
            "cycle_month": cycle_month,
            "balance_start": round(balance, 2),
            "interest": round(interest, 2),
            "min_payment": round(min_payment, 2),
            "balance_end": round(new_balance, 2),
        }

        if cycle_month == CYCLE_LENGTH:
            self._save_persisted_state({"cycle_month": 1, "balance": START_BALANCE})
        else:
            self._save_persisted_state({"cycle_month": cycle_month + 1, "balance": new_balance})

        return result
