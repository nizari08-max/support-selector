# =============================================================================
# drawing_index.py
# Support Code → Drawing Reference Number Mapping
# Standard: JESA Piping Support Standard Rev A  |  Document: QW2507-00-PE-STD-00001
# Drawing number prefix: JS-PE-DPS-
# =============================================================================
#
# HOW TO READ THE DRAWING NUMBERS:
#   The drawing index is on pages 3–8 of QW2507-00-PE-STD-00001.
#   Each support code maps to one or more drawing sheets.
#   Some supports have two sheets: -001 (welded) and -002 (bolted/alternative).
#
# FORMAT OF THIS DICT:
#   DRAWING_INDEX["SH01"] → list of full drawing reference strings
# =============================================================================

DRAWING_PREFIX = "JS-PE-DPS-"

DRAWING_INDEX = {
    # -------------------------------------------------------------------------
    # BEARING PLATES
    # -------------------------------------------------------------------------
    "BP02":  [f"{DRAWING_PREFIX}0321"],

    # -------------------------------------------------------------------------
    # WEAR PAD ASSEMBLIES
    # -------------------------------------------------------------------------
    "WA01":  [f"{DRAWING_PREFIX}0322-001", f"{DRAWING_PREFIX}0322-002"],
    "WA02":  [f"{DRAWING_PREFIX}0323-001", f"{DRAWING_PREFIX}0323-002"],
    "WA03":  [f"{DRAWING_PREFIX}0324-001", f"{DRAWING_PREFIX}0324-002"],

    # -------------------------------------------------------------------------
    # PIPE SHOES (SH series)
    # -------------------------------------------------------------------------
    "SH01":  [f"{DRAWING_PREFIX}0327-001", f"{DRAWING_PREFIX}0327-002"],
    "SH02":  [f"{DRAWING_PREFIX}0328-001", f"{DRAWING_PREFIX}0328-002"],
    "SH03":  [f"{DRAWING_PREFIX}0329"],
    "SH04":  [f"{DRAWING_PREFIX}0330"],
    "SH05":  [f"{DRAWING_PREFIX}0331"],

    # -------------------------------------------------------------------------
    # SHOE CLAMPS / SADDLE SUPPORTS (SC series)
    # -------------------------------------------------------------------------
    "SC01":  [f"{DRAWING_PREFIX}0342"],
    "SC02":  [f"{DRAWING_PREFIX}0343"],
    "SC03":  [f"{DRAWING_PREFIX}0344"],
    "SC04":  [f"{DRAWING_PREFIX}0345"],
    "SC05":  [f"{DRAWING_PREFIX}0346"],
    "SC06":  [f"{DRAWING_PREFIX}0347"],
    "SC07":  [f"{DRAWING_PREFIX}0348"],
    "SC08":  [f"{DRAWING_PREFIX}0349"],

    # -------------------------------------------------------------------------
    # GUIDE SUPPORTS (GL series)
    # -------------------------------------------------------------------------
    "GL01":  [f"{DRAWING_PREFIX}0357-001", f"{DRAWING_PREFIX}0357-002"],
    "GL02":  [f"{DRAWING_PREFIX}0358"],

    # -------------------------------------------------------------------------
    # LINE STOP SUPPORTS (LS series)
    # -------------------------------------------------------------------------
    "LS01":  [f"{DRAWING_PREFIX}0359-001", f"{DRAWING_PREFIX}0359-002"],
    "LS02":  [f"{DRAWING_PREFIX}0360"],
    "LS03":  [f"{DRAWING_PREFIX}0361"],

    # -------------------------------------------------------------------------
    # HOLD DOWN / GUIDE-HOLD SUPPORTS (GH series)
    # -------------------------------------------------------------------------
    "GH01":  [f"{DRAWING_PREFIX}0362"],
    "GH02":  [f"{DRAWING_PREFIX}0363"],

    # -------------------------------------------------------------------------
    # FRP CLAMP SHOES (CF series)
    # -------------------------------------------------------------------------
    "CF01":  [f"{DRAWING_PREFIX}0369"],
    "CF02":  [f"{DRAWING_PREFIX}0370"],
    "CF03":  [f"{DRAWING_PREFIX}0371"],
    "CF04":  [f"{DRAWING_PREFIX}0372"],   # FRP Clamp Shoe for Line Stop — verify sheet number
}


def get_drawings(support_code: str) -> list:
    """
    Return drawing reference numbers for a given support code or compound support string.

    Extracts all drawing codes (e.g. SH01, GL02, CF04) from the string using a
    regex, then looks each one up in DRAWING_INDEX.  Codes not in the index are
    silently skipped.  Results are de-duplicated and ordered by first appearance.

    Examples:
        get_drawings("WELDED SHOE (SH01/SH05) + WEAR PAD (WA01)")
            → ["JS-PE-DPS-0327-001", "JS-PE-DPS-0327-002",
               "JS-PE-DPS-0331",
               "JS-PE-DPS-0322-001", "JS-PE-DPS-0322-002"]

        get_drawings("GL01 + PR01/PR02 or WA01 (if applicable)")
            → ["JS-PE-DPS-0357-001", "JS-PE-DPS-0357-002",
               "JS-PE-DPS-0322-001", "JS-PE-DPS-0322-002"]

        get_drawings("DIRECT REST") → []
    """
    import re
    if not support_code:
        return []

    # Match codes like SH01, GL02, CF04 — 2 uppercase letters + 2 digits
    codes = re.findall(r'\b([A-Z]{2}\d{2})\b', support_code.upper())

    seen = set()
    drawings = []
    for code in codes:
        if code not in seen:
            seen.add(code)
            drawings.extend(DRAWING_INDEX.get(code, []))

    return drawings
