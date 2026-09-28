"""Shared data, geometry, visual and interaction constants."""

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

# Geographic scope and the binary land classifier. Elevation is never rendered.
MAP_BOUNDS = (113.80, 22.13, 114.46, 22.58)
MAP_CRS = "EPSG:32650"
TERRAIN_ZOOM = 10
TERRAIN_DOWNSAMPLE = 2
DOMAIN_STRIDE = 1
LAND_THRESHOLD_M = 2.0

# Fixed ranges make dates directly comparable.
TEMPERATURE_RANGE_C = (14.0, 28.0)
RAINFALL_RANGE_MM = (0.0, 67.0)
TEMPERATURE_BASELINE_C = 14.0
RAINFALL_BASELINE_MM = 0.0
TEMPERATURE_FADE_WIDTH_C = 3.5
RAINFALL_FADE_WIDTH_MM = 8.0
TEMPERATURE_IDW_POWER = 1.5
TEMPERATURE_IDW_NEIGHBOURS = 20
RAINFALL_IDW_POWER = 2.5
RAINFALL_IDW_NEIGHBOURS = 8
INTERPOLATION_EXACT_TOLERANCE_M = 0.05

# Y is the only height axis. Heights are fractions of the horizontal map span.
TEMPERATURE_HEIGHT_FRACTION = 0.18
RAINFALL_HEIGHT_FRACTION = 0.18

SCREENSHOT_DAY_INDEX = 23  # 24 April, the wettest summed station-day.
AUTOPLAY_INTERVAL_S = 0.9
AUTOPLAY_RESUME_DELAY_S = 2.0
CURSOR_INTERVAL_S = 1.0 / 30.0
CAMERA_PITCH_RANGE_DEG = (-60.0, 60.0)
INITIAL_CAMERA_PITCH_DEG = 28.0
CAMERA_DISTANCE_FACTOR = 1.72
DEPTH_FOG_START = 0.72
DEPTH_FOG_END = 0.995
DEPTH_FOG_STRENGTH = 0.68

# The Y=0 reference is a two-scale grid; alpha falls to zero at its perimeter.
GRID_MINOR_DIVISIONS = 24
GRID_MAJOR_EVERY = 4
GRID_MINOR_OPACITY = 0.19
GRID_MAJOR_OPACITY = 0.42
GRID_EDGE_FADE_START = 0.48

BACKGROUND_COLOUR = "#07151b"
BACKGROUND_TOP_COLOUR = "#163139"
LAND_COLOUR = "#c7d8c0"
SEA_COLOUR = "#eaf3f5"
COASTLINE_COLOUR = "#31515a"
DISTRICT_COLOUR = "#5e7479"
STATION_COLOUR = "#f7fbfc"
HIGHLIGHT_COLOUR = "#ffe36b"
TEMPERATURE_OPACITY = 0.62
RAINFALL_OPACITY = 0.52
LAND_OPACITY = 0.40
SEA_OPACITY = 0.08
TEMPERATURE_COLOURS = ["#493a86", "#a5538f", "#e07a4f", "#f4d35e"]
RAINFALL_COLOURS = ["#bfe8f2", "#3b9bc2", "#164a7b"]

WEB_SCHEMA_VERSION = 2
WEB_ARTIFACT_TARGET_BYTES = 20 * 1024 * 1024
