"""Fetches the current 10-year US Treasury yield from the US Treasury's public daily rates CSV each tick."""

import csv
import io
import urllib.request
from datetime import datetime, timezone

from harness.shitpost_base import Shitpost

URL_TEMPLATE = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
    "daily-treasury-rates.csv/{year}/all?type=daily_treasury_yield_curve"
    "&field_tdr_date_value={year}&page&_format=csv"
)


def _parse(csv_text):
    reader = csv.reader(io.StringIO(csv_text))
    header = next(reader)
    column_index = header.index("10 Yr")
    row = next(reader)
    return {"date": row[0], "yield_10yr": float(row[column_index])}


class TreasuryYieldPlugin(Shitpost):
    """Fetch and emit the current 10-year Treasury yield. Skips the tick on any fetch failure."""

    name = "treasury-yield"
    internal = False
    commit_template = "10yr treasury: {yield_10yr}%"

    def produce(self):
        try:
            year = datetime.now(timezone.utc).year
            url = URL_TEMPLATE.format(year=year)
            with urllib.request.urlopen(url, timeout=10) as response:
                csv_text = response.read().decode("utf-8")
            return _parse(csv_text)
        except Exception:
            return None
