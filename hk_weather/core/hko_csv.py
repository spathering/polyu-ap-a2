"""Low-level parsing shared by audit and preparation pipelines."""

import csv
import datetime as dt


MISSING_VALUES = {"", "***", "M", "N/A", "NA"}
TRACE_VALUE = "Trace"


def expected_dates(year, month):
    """Return every calendar date in one month."""
    first = dt.date(year, month, 1)
    after = dt.date(year + 1, 1, 1) if month == 12 else dt.date(year, month + 1, 1)
    return [first + dt.timedelta(days=i) for i in range((after - first).days)]


def read_daily_rows(path, year, month):
    """Read a bilingual HKO CSV and keep rows for one month."""
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.reader(handle):
            if len(row) < 4 or not all(cell.strip().isdigit() for cell in row[:3]):
                continue
            row_year, row_month, row_day = map(int, row[:3])
            if (row_year, row_month) != (year, month):
                continue
            rows.append({
                "date": dt.date(row_year, row_month, row_day),
                "value": row[3].strip(),
                "flag": row[4].strip() if len(row) > 4 else "",
            })
    return rows
