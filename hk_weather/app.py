"""Temporary template renderer; replaced by the planned PyVista scene next."""

import csv

import matplotlib.pyplot as plt

from hk_weather.core.paths import DATA, OUT


FILE = "hko-daily-mean-temperature-2026.csv"
PICTURE = "plot.png"


def rows(path):
    """Keep HKO table rows that begin with a year."""
    kept = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for line in csv.reader(handle):
            if line and line[0].isdigit():
                kept.append(line)
    return kept


def main():
    """Run the untouched template plot until the 3D renderer replaces it."""
    table = rows(DATA / FILE)
    days, values = [], []
    for index, (_, _, _, value, _) in enumerate(table):
        if value == "***":
            continue
        days.append(index + 1)
        values.append(float(value))

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(days, values, color="#d6591d", linewidth=1.5)
    ax.set_xlabel("day of 2026")
    ax.set_ylabel("daily mean temperature, °C")
    ax.set_title("Hong Kong Observatory, 2026 so far")
    fig.tight_layout()

    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / PICTURE, dpi=150)
    plt.show()
