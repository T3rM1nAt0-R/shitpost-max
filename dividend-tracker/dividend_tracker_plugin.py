"""Simulates dividend yield and quarterly payout for a fixed cycling list of tickers. No live network calls."""

from harness.shitpost_base import Shitpost

TICKERS = [
    ("AAPL", 180.0, 0.005),
    ("MSFT", 420.0, 0.007),
    ("JNJ", 155.0, 0.03),
    ("KO", 62.0, 0.031),
    ("PG", 165.0, 0.024),
    ("XOM", 115.0, 0.033),
]


class DividendTrackerPlugin(Shitpost):
    """Emit simulated dividend info for one ticker per tick, cycling through the list."""

    name = "dividend-tracker"
    internal = False
    commit_template = "dividend {ticker}: payout {quarterly_payout}"

    def produce(self) -> dict:
        state = self._load_persisted_state({"index": 0})
        index = state["index"]

        ticker, price, yld = TICKERS[index]
        quarterly_payout = price * yld / 4

        result = {
            "ticker": ticker,
            "price": price,
            "annual_yield": yld,
            "quarterly_payout": round(quarterly_payout, 4),
        }

        self._save_persisted_state({"index": (index + 1) % len(TICKERS)})

        return result
