"""Audit HKO daily files and compare completed months."""

import argparse
from collections import Counter

from hk_weather.core.config import (
    EXCLUDED_STATIONS,
    MONTH,
    SOURCE_STATIONS,
    STATIONS,
    YEAR,
)
from hk_weather.core.hko_csv import (
    MISSING_VALUES,
    TRACE_VALUE,
    expected_dates,
    read_daily_rows,
)
from hk_weather.core.paths import RAINFALL, TEMPERATURE


def inspect(path, expected, year, month):
    """Summarise date coverage and value quality for one raw file."""
    rows = read_daily_rows(path, year, month)
    counts = Counter(row["date"] for row in rows)
    missing_dates = sorted(set(expected) - set(counts))
    duplicate_dates = sorted(day for day, count in counts.items() if count > 1)
    missing_values = sorted(row["date"] for row in rows if row["value"] in MISSING_VALUES)
    numeric = []
    invalid = []
    trace_dates = []
    for row in rows:
        if row["value"] in MISSING_VALUES:
            continue
        if row["value"] == TRACE_VALUE:
            trace_dates.append(row["date"])
            continue
        try:
            numeric.append(float(row["value"]))
        except ValueError:
            invalid.append((row["date"], row["value"]))
    incomplete = sorted(row["date"] for row in rows if row["flag"] == "#")
    return {
        "rows": len(rows),
        "missing_dates": missing_dates,
        "duplicate_dates": duplicate_dates,
        "missing_values": missing_values,
        "invalid": invalid,
        "incomplete": incomplete,
        "trace_dates": trace_dates,
        "flags": Counter(row["flag"] or "(blank)" for row in rows),
        "minimum": min(numeric) if numeric else None,
        "maximum": max(numeric) if numeric else None,
    }


def short_dates(days):
    return ",".join(day.strftime("%d") for day in days) if days else "-"


def complete(result):
    return not any(result[key] for key in (
        "missing_dates", "duplicate_dates", "missing_values", "invalid", "incomplete"
    ))


def audit_month(month, stations, detailed=False):
    expected = expected_dates(YEAR, month)
    problems = 0
    complete_pairs = 0
    trace_count = 0
    all_flags = {"temperature": Counter(), "rainfall": Counter()}

    if detailed:
        print(f"HKO data audit — {YEAR}-{month:02}, {len(expected)} expected days")
        print("station  temp unavailable  rain unavailable  paired  ranges")

    for station in stations:
        temp_path = TEMPERATURE / f"daily-mean-temperature-{station}-{YEAR}.csv"
        rain_path = RAINFALL / f"daily-total-rainfall-{station}-{YEAR}.csv"
        absent = [path for path in (temp_path, rain_path) if not path.is_file()]
        if absent:
            problems += 1
            if detailed:
                print(f"{station:7} FILE MISSING — {', '.join(path.name for path in absent)}")
            continue

        temp = inspect(temp_path, expected, YEAR, month)
        rain = inspect(rain_path, expected, YEAR, month)
        all_flags["temperature"].update(temp["flags"])
        all_flags["rainfall"].update(rain["flags"])
        trace_count += len(rain["trace_dates"])

        paired_bad = set(temp["missing_dates"] + temp["missing_values"] +
                         temp["incomplete"] + rain["missing_dates"] +
                         rain["missing_values"] + rain["incomplete"])
        paired = len(expected) - len(paired_bad)
        if complete(temp) and complete(rain):
            complete_pairs += 1
        else:
            problems += 1

        if detailed:
            temp_unavailable = sorted(set(temp["missing_dates"] + temp["missing_values"] + temp["incomplete"]))
            rain_unavailable = sorted(set(rain["missing_dates"] + rain["missing_values"] + rain["incomplete"]))
            temp_range = f"{temp['minimum']:.1f}..{temp['maximum']:.1f} C" if temp["minimum"] is not None else "-"
            rain_range = f"{rain['minimum']:.1f}..{rain['maximum']:.1f} mm" if rain["minimum"] is not None else "-"
            print(
                f"{station:7} {temp['rows']:2}/{short_dates(temp_unavailable):<7} "
                f"{rain['rows']:2}/{short_dates(rain_unavailable):<7} "
                f"{paired:2} days  {temp_range}; {rain_range}"
            )
            if temp["duplicate_dates"] or rain["duplicate_dates"]:
                print(f"         duplicates temp={short_dates(temp['duplicate_dates'])} "
                      f"rain={short_dates(rain['duplicate_dates'])}")
            if temp["invalid"] or rain["invalid"]:
                print(f"         invalid temp={temp['invalid']} rain={rain['invalid']}")

    if detailed:
        print("\ncompleteness flags")
        for kind, flags in all_flags.items():
            print(f"  {kind}: {dict(sorted(flags.items()))}")
        print(f"  rainfall Trace values: {trace_count} (valid observations below 0.05 mm)")
        print(f"\nfully complete station pairs: {complete_pairs}/{len(stations)}")
        print(f"stations with a file/date/value/flag problem: {problems}")
    return complete_pairs, problems, trace_count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--months", action="store_true", help="compare completed months")
    args = parser.parse_args()

    if args.months:
        print(f"HKO completed-month comparison — {YEAR}")
        print("month  complete station pairs  station pairs with issues  Trace values")
        for month in range(1, 9):
            good, bad, traces = audit_month(month, SOURCE_STATIONS)
            print(f"{month:02}     {good:2}/{len(SOURCE_STATIONS):2}                  {bad:2}                         {traces:3}")
        return

    audit_month(MONTH, STATIONS, detailed=True)
    print("\nexcluded after the candidate-month audit")
    for station, reason in EXCLUDED_STATIONS.items():
        print(f"  {station}: {reason}")
