"""Shows how a fixed amount of money erodes under a fixed inflation rate over 30 years, then resets to year 0."""

from harness.shitpost_base import Shitpost

AMOUNT = 100000.0
ANNUAL_RATE = 0.06
MAX_YEAR = 30


class InflationCalculatorPlugin(Shitpost):
    """Emit one year's eroded value per tick, cycling every MAX_YEAR+1 years."""

    name = "inflation-calculator"
    internal = False
    commit_template = "inflation year {year}: {eroded_value}"

    def produce(self) -> dict:
        state = self._load_persisted_state({"year": 0})
        year = state["year"]

        value = AMOUNT / (1 + ANNUAL_RATE) ** year

        result = {
            "year": year,
            "eroded_value": round(value, 2),
        }

        if year == MAX_YEAR:
            self._save_persisted_state({"year": 0})
        else:
            self._save_persisted_state({"year": year + 1})

        return result
