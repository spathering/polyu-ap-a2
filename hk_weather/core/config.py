"""Shared scope for the selected 2026 HKO dataset."""

YEAR = 2026
MONTH = 4

SOURCE_STATIONS = {
    "CCH": "Cheung Chau",
    "HKA": "Hong Kong International Airport",
    "HKO": "Hong Kong Observatory",
    "JKB": "Tseung Kwan O",
    "KP": "King's Park",
    "KSC": "Kau Sai Chau",
    "LFS": "Lau Fau Shan",
    "PEN": "Peng Chau",
    "PLC": "Tai Mei Tuk",
    "SEK": "Shek Kong",
    "SHA": "Sha Tin",
    "SKW": "Shau Kei Wan",
    "SSH": "Sheung Shui",
    "SSP": "Sham Shui Po",
    "TC": "Tate's Cairn",
    "TKL": "Ta Kwu Ling",
    "TMS": "Tai Mo Shan",
    "TU1": "Tuen Mun Children and Juvenile Home",
    "TWN": "Tsuen Wan",
    "TYW": "Pak Tam Chung (Tsak Yue Wu)",
    "VP1": "The Peak",
    "WGL": "Waglan Island",
    "WLP": "Wetland Park",
}

EXCLUDED_STATIONS = {
    "SKW": "rainfall incomplete on 2026-04-11 and 2026-04-12",
    "WLP": "temperature incomplete on 2026-04-08",
}

STATIONS = {
    code: name for code, name in SOURCE_STATIONS.items()
    if code not in EXCLUDED_STATIONS
}
