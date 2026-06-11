"""
Eurocode 3 structural steel profile dimensions.

Source: EN 10365:2017 (Hot rolled steel channels, I and H sections — Dimensions and masses),
        as published at https://eurocodeapplied.com/design/en1993/ipe-hea-heb-hem-design-properties

IPE dimensions are verified directly from the EurocodeApplied reference page.
HEA, HEB, HEM dimensions follow EN 10365:2017 (same standard cited by EurocodeApplied).

For the rack column width formula the relevant dimension is flange width b (mm).
"""

# Each profile entry: {"size": str, "h": int, "b": int, "tw": float, "tf": float}
#   h  = total height (mm)
#   b  = flange width (mm)  ← used as steel_column_mm in the rack formula
#   tw = web thickness (mm)
#   tf = flange thickness (mm)

PROFILES = {
    "IPE": [
        {"size": "80",  "h":  80, "b":  46, "tw":  3.8, "tf":  5.2},
        {"size": "100", "h": 100, "b":  55, "tw":  4.1, "tf":  5.7},
        {"size": "120", "h": 120, "b":  64, "tw":  4.4, "tf":  6.3},
        {"size": "140", "h": 140, "b":  73, "tw":  4.7, "tf":  6.9},
        {"size": "160", "h": 160, "b":  82, "tw":  5.0, "tf":  7.4},
        {"size": "180", "h": 180, "b":  91, "tw":  5.3, "tf":  8.0},
        {"size": "200", "h": 200, "b": 100, "tw":  5.6, "tf":  8.5},
        {"size": "220", "h": 220, "b": 110, "tw":  5.9, "tf":  9.2},
        {"size": "240", "h": 240, "b": 120, "tw":  6.2, "tf":  9.8},
        {"size": "270", "h": 270, "b": 135, "tw":  6.6, "tf": 10.2},
        {"size": "300", "h": 300, "b": 150, "tw":  7.1, "tf": 10.7},
        {"size": "330", "h": 330, "b": 160, "tw":  7.5, "tf": 11.5},
        {"size": "360", "h": 360, "b": 170, "tw":  8.0, "tf": 12.7},
        {"size": "400", "h": 400, "b": 180, "tw":  8.6, "tf": 13.5},
        {"size": "450", "h": 450, "b": 190, "tw":  9.4, "tf": 14.6},
        {"size": "500", "h": 500, "b": 200, "tw": 10.2, "tf": 16.0},
        {"size": "550", "h": 550, "b": 210, "tw": 11.1, "tf": 17.2},
        {"size": "600", "h": 600, "b": 220, "tw": 12.0, "tf": 19.0},
    ],
    "HEA": [
        {"size": "100",  "h":   96, "b": 100, "tw":  5.0, "tf":  8.0},
        {"size": "120",  "h":  114, "b": 120, "tw":  5.0, "tf":  8.0},
        {"size": "140",  "h":  133, "b": 140, "tw":  5.5, "tf":  8.5},
        {"size": "160",  "h":  152, "b": 160, "tw":  6.0, "tf":  9.0},
        {"size": "180",  "h":  171, "b": 180, "tw":  6.0, "tf":  9.5},
        {"size": "200",  "h":  190, "b": 200, "tw":  6.5, "tf": 10.0},
        {"size": "220",  "h":  210, "b": 220, "tw":  7.0, "tf": 11.0},
        {"size": "240",  "h":  230, "b": 240, "tw":  7.5, "tf": 12.0},
        {"size": "260",  "h":  250, "b": 260, "tw":  7.5, "tf": 12.5},
        {"size": "280",  "h":  270, "b": 280, "tw":  8.0, "tf": 13.0},
        {"size": "300",  "h":  290, "b": 300, "tw":  8.5, "tf": 14.0},
        {"size": "320",  "h":  310, "b": 300, "tw":  9.0, "tf": 15.5},
        {"size": "340",  "h":  330, "b": 300, "tw":  9.5, "tf": 16.5},
        {"size": "360",  "h":  350, "b": 300, "tw": 10.0, "tf": 17.5},
        {"size": "400",  "h":  390, "b": 300, "tw": 11.0, "tf": 19.0},
        {"size": "450",  "h":  440, "b": 300, "tw": 11.5, "tf": 21.0},
        {"size": "500",  "h":  490, "b": 300, "tw": 12.0, "tf": 23.0},
        {"size": "550",  "h":  540, "b": 300, "tw": 12.5, "tf": 24.0},
        {"size": "600",  "h":  590, "b": 300, "tw": 13.0, "tf": 25.0},
        {"size": "650",  "h":  640, "b": 300, "tw": 13.5, "tf": 26.0},
        {"size": "700",  "h":  690, "b": 300, "tw": 14.5, "tf": 27.0},
        {"size": "800",  "h":  790, "b": 300, "tw": 15.0, "tf": 28.0},
        {"size": "900",  "h":  890, "b": 300, "tw": 16.0, "tf": 30.0},
        {"size": "1000", "h":  990, "b": 300, "tw": 16.5, "tf": 31.0},
    ],
    "HEB": [
        {"size": "100",  "h":  100, "b": 100, "tw":  6.0, "tf": 10.0},
        {"size": "120",  "h":  120, "b": 120, "tw":  6.5, "tf": 11.0},
        {"size": "140",  "h":  140, "b": 140, "tw":  7.0, "tf": 12.0},
        {"size": "160",  "h":  160, "b": 160, "tw":  8.0, "tf": 13.0},
        {"size": "180",  "h":  180, "b": 180, "tw":  8.5, "tf": 14.0},
        {"size": "200",  "h":  200, "b": 200, "tw":  9.0, "tf": 15.0},
        {"size": "220",  "h":  220, "b": 220, "tw":  9.5, "tf": 16.0},
        {"size": "240",  "h":  240, "b": 240, "tw": 10.0, "tf": 17.0},
        {"size": "260",  "h":  260, "b": 260, "tw": 10.0, "tf": 17.5},
        {"size": "280",  "h":  280, "b": 280, "tw": 10.5, "tf": 18.0},
        {"size": "300",  "h":  300, "b": 300, "tw": 11.0, "tf": 19.0},
        {"size": "320",  "h":  320, "b": 300, "tw": 11.5, "tf": 20.5},
        {"size": "340",  "h":  340, "b": 300, "tw": 12.0, "tf": 21.5},
        {"size": "360",  "h":  360, "b": 300, "tw": 12.5, "tf": 22.5},
        {"size": "400",  "h":  400, "b": 300, "tw": 13.5, "tf": 24.0},
        {"size": "450",  "h":  450, "b": 300, "tw": 14.0, "tf": 26.0},
        {"size": "500",  "h":  500, "b": 300, "tw": 14.5, "tf": 28.0},
        {"size": "550",  "h":  550, "b": 300, "tw": 15.0, "tf": 29.0},
        {"size": "600",  "h":  600, "b": 300, "tw": 15.5, "tf": 30.0},
        {"size": "650",  "h":  650, "b": 300, "tw": 16.0, "tf": 31.0},
        {"size": "700",  "h":  700, "b": 300, "tw": 17.0, "tf": 32.0},
        {"size": "800",  "h":  800, "b": 300, "tw": 17.5, "tf": 33.0},
        {"size": "900",  "h":  900, "b": 300, "tw": 18.5, "tf": 35.0},
        {"size": "1000", "h": 1000, "b": 300, "tw": 19.0, "tf": 36.0},
    ],
    "HEM": [
        {"size": "100",  "h":  120, "b": 106, "tw": 12.0, "tf": 20.0},
        {"size": "120",  "h":  140, "b": 126, "tw": 12.5, "tf": 21.0},
        {"size": "140",  "h":  160, "b": 146, "tw": 13.0, "tf": 22.0},
        {"size": "160",  "h":  180, "b": 166, "tw": 14.0, "tf": 23.0},
        {"size": "180",  "h":  200, "b": 186, "tw": 14.5, "tf": 24.0},
        {"size": "200",  "h":  220, "b": 206, "tw": 15.0, "tf": 25.0},
        {"size": "220",  "h":  240, "b": 226, "tw": 15.5, "tf": 26.0},
        {"size": "240",  "h":  270, "b": 248, "tw": 18.0, "tf": 32.0},
        {"size": "260",  "h":  290, "b": 268, "tw": 18.0, "tf": 32.5},
        {"size": "280",  "h":  310, "b": 288, "tw": 18.5, "tf": 33.0},
        {"size": "300",  "h":  340, "b": 310, "tw": 21.0, "tf": 39.0},
        {"size": "320",  "h":  359, "b": 309, "tw": 21.0, "tf": 40.0},
        {"size": "340",  "h":  377, "b": 309, "tw": 21.0, "tf": 40.0},
        {"size": "360",  "h":  395, "b": 308, "tw": 21.0, "tf": 40.0},
        {"size": "400",  "h":  432, "b": 307, "tw": 21.0, "tf": 40.0},
        {"size": "450",  "h":  478, "b": 307, "tw": 21.0, "tf": 40.0},
        {"size": "500",  "h":  524, "b": 306, "tw": 21.0, "tf": 40.0},
        {"size": "550",  "h":  572, "b": 306, "tw": 21.0, "tf": 40.0},
        {"size": "600",  "h":  620, "b": 305, "tw": 21.0, "tf": 40.0},
        {"size": "650",  "h":  668, "b": 305, "tw": 21.0, "tf": 40.0},
        {"size": "700",  "h":  716, "b": 304, "tw": 21.0, "tf": 40.0},
        {"size": "800",  "h":  814, "b": 303, "tw": 21.0, "tf": 40.0},
        {"size": "900",  "h":  910, "b": 302, "tw": 21.0, "tf": 40.0},
        {"size": "1000", "h": 1008, "b": 302, "tw": 21.0, "tf": 40.0},
    ],
}

PROFILE_FAMILIES = list(PROFILES.keys())  # ["IPE", "HEA", "HEB", "HEM"]


def get_profile_width(family: str, size: str) -> int:
    """Return flange width b (mm) for the given Eurocode profile family and size."""
    family = family.upper()
    if family not in PROFILES:
        raise ValueError(f"Unknown profile family '{family}'. Available: {', '.join(PROFILES)}")
    for p in PROFILES[family]:
        if p["size"] == size:
            return p["b"]
    raise ValueError(f"Profile {family} {size} not found in database.")


def profiles_for_js() -> dict:
    """Return a lightweight dict suitable for JSON serialisation in the template."""
    return {
        family: [{"size": p["size"], "b": p["b"]} for p in entries]
        for family, entries in PROFILES.items()
    }
