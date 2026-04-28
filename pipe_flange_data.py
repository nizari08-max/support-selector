"""
ASME pipe and flange outside diameter data.

Sources:
  - ASME B36.10M-2000  : Pipe outside diameters (DN 15 to DN 1000)
  - ASME B16.5-2009    : Flange outside diameters (DN 15 to DN 600)
  - ASME B16.47-2017   : Flange outside diameters (DN 650 to DN 1000)
                         in both Series A (MSS SP-44) and Series B (API 605)

All values are in millimeters, extracted directly from the reference
"PIPE SPACING & RACK WIDTH DETERMINATION CALCULATOR" Excel workbook
(by Boutrih Boujemaa, April 2024 Rev. 1) so that this module produces
bit-identical results to the source spreadsheet.

Note: pipe ODs are stored as integers (mm), matching the reference
workbook's rounded values. The true ASME B36.10M values include
sub-millimeter decimals (e.g. DN300 OD is 323.85 mm); the reference
sheet rounds these to whole millimeters (324 mm). We follow the
reference convention for exact reproducibility.
"""

# -----------------------------------------------------------------------------
# Pipe Outside Diameter (ASME B36.10M, integer mm as used in reference Excel)
# -----------------------------------------------------------------------------
PIPE_OD_MM = {
    15:    21,
    20:    27,
    25:    33,
    32:    42,
    40:    48,
    50:    60,
    65:    73,
    80:    89,
    90:   102,    # NPS 3.5"
    100:  114,
    125:  141,    # NPS 5"
    150:  168,
    200:  219,
    250:  273,
    300:  324,
    350:  356,
    400:  406,
    450:  457,
    500:  508,
    600:  610,
    650:  660,
    700:  711,
    750:  762,
    800:  813,
    850:  864,
    900:  914,
    950:  965,
    1000: 1016,
}

# Available DN sizes in order, for UI dropdowns
DN_SIZES = sorted(PIPE_OD_MM.keys())

# -----------------------------------------------------------------------------
# Flange Outside Diameter
#
# Keys are either integers (B16.5 ratings: 150, 300, 400, 600, 900, 1500, 2500)
# or strings (B16.47 ratings: '150A', '300A', '400A', '600A', '900A' for Series A;
# '150B', '300B', '400B', '600B', '900B' for Series B).
#
# A combination missing from a DN's dict means that flange size is not
# standardized for that pipe size.
#
# NOTE: DN250 #600 = 340 in the reference Excel. This appears to be a
# typo (the standard B16.5 value is 510 mm). It is preserved here as-is
# to ensure bit-identical output to the reference workbook. Users should
# be aware of this when designing for DN250 #600 flanges.
# -----------------------------------------------------------------------------
FLANGE_OD_MM = {
    # ---- ASME B16.5 (DN 15 to DN 600) ----
    15:  {150: 90,  300: 95,  400: 95,  600: 95,  900: 120, 1500: 120, 2500: 135},
    20:  {150: 100, 300: 115, 400: 115, 600: 115, 900: 130, 1500: 130, 2500: 140},
    25:  {150: 110, 300: 125, 400: 125, 600: 125, 900: 150, 1500: 150, 2500: 160},
    32:  {150: 115, 300: 135, 400: 135, 600: 135, 900: 160, 1500: 160, 2500: 185},
    40:  {150: 125, 300: 155, 400: 155, 600: 155, 900: 180, 1500: 180, 2500: 205},
    50:  {150: 150, 300: 165, 400: 165, 600: 165, 900: 215, 1500: 215, 2500: 235},
    65:  {150: 180, 300: 190, 400: 190, 600: 190, 900: 245, 1500: 245, 2500: 265},
    80:  {150: 190, 300: 210, 400: 210, 600: 210, 900: 240, 1500: 265, 2500: 305},
    90:  {150: 215, 300: 230, 400: 230, 600: 230},
    100: {150: 230, 300: 255, 400: 255, 600: 275, 900: 290, 1500: 310, 2500: 355},
    125: {150: 255, 300: 280, 400: 280, 600: 330, 900: 350, 1500: 375, 2500: 420},
    150: {150: 280, 300: 320, 400: 320, 600: 355, 900: 380, 1500: 395, 2500: 485},
    200: {150: 345, 300: 380, 400: 380, 600: 420, 900: 470, 1500: 485, 2500: 550},
    250: {150: 405, 300: 445, 400: 445, 600: 340, 900: 545, 1500: 585, 2500: 675},  # 600 value preserved from source
    300: {150: 485, 300: 520, 400: 520, 600: 560, 900: 610, 1500: 675, 2500: 760},
    350: {150: 535, 300: 585, 400: 585, 600: 605, 900: 640, 1500: 750},
    400: {150: 595, 300: 650, 400: 650, 600: 685, 900: 705, 1500: 825},
    450: {150: 635, 300: 710, 400: 710, 600: 745, 900: 785, 1500: 915},
    500: {150: 700, 300: 775, 400: 775, 600: 815, 900: 855, 1500: 985},
    600: {150: 815, 300: 915, 400: 915, 600: 940, 900: 1040, 1500: 1170},

    # ---- ASME B16.47 Series A & B (DN 650 to DN 1000) ----
    650:  {'150A': 870,  '300A': 970,  '400A': 970,  '600A': 1015, '900A': 1085,
           '150B': 785,  '300B': 865,  '400B': 850,  '600B': 890,  '900B': 1020},
    700:  {'150A': 925,  '300A': 1035, '400A': 1035, '600A': 1075, '900A': 1170,
           '150B': 835,  '300B': 920,  '400B': 915,  '600B': 950,  '900B': 1105},
    750:  {'150A': 985,  '300A': 1090, '400A': 1090, '600A': 1130, '900A': 1230,
           '150B': 885,  '300B': 990,  '400B': 970,  '600B': 1020, '900B': 1180},
    800:  {'150A': 1060, '300A': 1150, '400A': 1150, '600A': 1195, '900A': 1315,
           '150B': 940,  '300B': 1055, '400B': 1035, '600B': 1085, '900B': 1240},
    850:  {'150A': 1110, '300A': 1205, '400A': 1205, '600A': 1245, '900A': 1395,
           '150B': 1005, '300B': 1110, '400B': 1085, '600B': 1160, '900B': 1315},
    900:  {'150A': 1170, '300A': 1270, '400A': 1270, '600A': 1315, '900A': 1460,
           '150B': 1055, '300B': 1170, '400B': 1155, '600B': 1215, '900B': 1345},
    950:  {'150A': 1240, '300A': 1170, '400A': 1205, '600A': 1270, '900A': 1460,
           '150B': 1125, '300B': 1220},
    1000: {'150A': 1290, '300A': 1240, '400A': 1270, '600A': 1320, '900A': 1510,
           '150B': 1175, '300B': 1275},
}

# All distinct ratings across all DNs, in display order
FLANGE_RATINGS = [
    150, 300, 400, 600, 900, 1500, 2500,
    '150A', '300A', '400A', '600A', '900A',
    '150B', '300B', '400B', '600B', '900B',
]


def rating_label(rating):
    """Format a rating for display: 150 -> 'Class 150', '150A' -> 'Class 150 (Series A)'."""
    if isinstance(rating, int):
        return f"Class {rating}"
    if rating.endswith('A'):
        return f"Class {rating[:-1]} (Series A)"
    if rating.endswith('B'):
        return f"Class {rating[:-1]} (Series B)"
    return f"Class {rating}"


def get_pipe_od(dn):
    """Return pipe OD in mm for a given DN. Raises KeyError if DN not in table."""
    return PIPE_OD_MM[dn]


def get_flange_od(dn, rating):
    """
    Return flange OD in mm for a given DN and rating.
    Returns None if the combination is not standardized.
    Rating may be int (B16.5: 150, 300, 400, 600, 900, 1500, 2500) or
    string (B16.47: '150A'..'900A', '150B'..'900B').
    """
    return FLANGE_OD_MM.get(dn, {}).get(rating)


def available_ratings_for_dn(dn):
    """Return the list of ratings available for a given DN, in display order."""
    if dn not in FLANGE_OD_MM:
        return []
    available = FLANGE_OD_MM[dn].keys()
    return [r for r in FLANGE_RATINGS if r in available]
