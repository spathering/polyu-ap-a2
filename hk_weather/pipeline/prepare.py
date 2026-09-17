"""Create the tidy, strictly complete weather dataset."""

import csv
import html.parser
import re

from hk_weather.core.config import MONTH, STATIONS, YEAR
from hk_weather.core.hko_csv import MISSING_VALUES, TRACE_VALUE, expected_dates, read_daily_rows
from hk_weather.core.paths import DATA, PROJECT_ROOT, RAINFALL, STATION_PAGE, TEMPERATURE


OUTPUT = DATA / f"hk-weather-{YEAR}-{MONTH:02}.csv"
CODE_PATTERN = re.compile(r"\(([A-Z0-9]+)\)")
DMS_PATTERN = re.compile(r"(\d+)°(\d+)'(\d+)\"")


class StationTableParser(html.parser.HTMLParser):
    """Collect text cells from the HKO station tables."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = []
        self.row = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        elif tag == "td" and self.row is not None:
            self.cell = []
        elif tag == "br" and self.cell is not None:
            self.cell.append(" ")

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag == "td" and self.cell is not None and self.row is not None:
            self.row.append("".join(self.cell).strip())
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if self.row:
                self.rows.append(self.row)
            self.row = None


def dms_to_decimal(value):
    match = DMS_PATTERN.fullmatch(value.strip())
    if not match:
        raise ValueError(f"unrecognised coordinate: {value!r}")
    degrees, minutes, seconds = map(int, match.groups())
    return degrees + minutes / 60 + seconds / 3600


def station_metadata():
    parser = StationTableParser()
    parser.feed(STATION_PAGE.read_text(encoding="utf-8"))
    metadata = {}
    for row in parser.rows:
        if len(row) < 4:
            continue
        code_match = CODE_PATTERN.search(row[0])
        if not code_match:
            continue
        code = code_match.group(1)
        if code not in STATIONS or code in metadata:
            continue
        metadata[code] = {
            "latitude": dms_to_decimal(row[1]),
            "longitude": dms_to_decimal(row[2]),
            "elevation_m": float(row[3]),
        }
    missing = sorted(set(STATIONS) - set(metadata))
    if missing:
        raise RuntimeError(f"station metadata missing for: {', '.join(missing)}")
    return metadata


def indexed_rows(path):
    result = {}
    for row in read_daily_rows(path, YEAR, MONTH):
        if row["date"] in result:
            raise RuntimeError(f"duplicate date in {path.name}: {row['date']}")
        if row["value"] in MISSING_VALUES or row["flag"] != "C":
            raise RuntimeError(
                f"unusable value in {path.name}: {row['date']} "
                f"value={row['value']!r} flag={row['flag']!r}"
            )
        result[row["date"]] = row["value"]
    return result


def main():
    metadata = station_metadata()
    dates = expected_dates(YEAR, MONTH)
    output_rows = []

    for code, name in STATIONS.items():
        temperatures = indexed_rows(TEMPERATURE / f"daily-mean-temperature-{code}-{YEAR}.csv")
        rainfall = indexed_rows(RAINFALL / f"daily-total-rainfall-{code}-{YEAR}.csv")
        if set(temperatures) != set(dates) or set(rainfall) != set(dates):
            raise RuntimeError(f"date coverage is not complete for {code}")

        for day in dates:
            rain_value = rainfall[day]
            is_trace = rain_value == TRACE_VALUE
            output_rows.append({
                "date": day.isoformat(),
                "station": code,
                "station_name": name,
                "latitude": f"{metadata[code]['latitude']:.6f}",
                "longitude": f"{metadata[code]['longitude']:.6f}",
                "elevation_m": f"{metadata[code]['elevation_m']:.1f}",
                "mean_temperature_c": f"{float(temperatures[day]):.1f}",
                "total_rainfall_mm": "0.0" if is_trace else f"{float(rain_value):.1f}",
                "rainfall_trace": str(is_trace).lower(),
            })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"wrote {OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"rows: {len(output_rows)} = {len(STATIONS)} stations x {len(dates)} days")
    print(f"date range: {dates[0]} to {dates[-1]}")
    print(f"Trace rainfall rows retained: {sum(row['rainfall_trace'] == 'true' for row in output_rows)}")
