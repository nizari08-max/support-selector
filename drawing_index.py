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

import re

DRAWING_PREFIX = "JS-PE-DPS-"

DRAWING_INDEX = {
    # -------------------------------------------------------------------------
    # BEARING PLATES
    # -------------------------------------------------------------------------
    "BP02":  [f"{DRAWING_PREFIX}0321"],

    # -------------------------------------------------------------------------
    # WEAR PAD ASSEMBLIES
    # Sheets -001 and -002 are merged into a single ref (no suffix).
    # Clicking the chip opens a 2-page PDF (plan view + notes/table).
    # -------------------------------------------------------------------------
    "WA01":  [f"{DRAWING_PREFIX}0322"],
    "WA02":  [f"{DRAWING_PREFIX}0323"],
    "WA03":  [f"{DRAWING_PREFIX}0324"],

    # -------------------------------------------------------------------------
    # PIPE SHOES (SH series)
    # SH01/SH02 each have two sheets; merged into a single ref per drawing.
    # SH03/SH04 are already single refs pointing to 2 PDF pages (no suffix).
    # -------------------------------------------------------------------------
    "SH01":  [f"{DRAWING_PREFIX}0327"],
    "SH02":  [f"{DRAWING_PREFIX}0328"],
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
    # GL01 has two sheets; merged into a single ref.
    # -------------------------------------------------------------------------
    "GL01":  [f"{DRAWING_PREFIX}0357"],
    "GL02":  [f"{DRAWING_PREFIX}0358"],

    # -------------------------------------------------------------------------
    # LINE STOP SUPPORTS (LS series)
    # LS01 has two sheets; merged into a single ref.
    # -------------------------------------------------------------------------
    "LS01":  [f"{DRAWING_PREFIX}0359"],
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
    "CF04":  [f"{DRAWING_PREFIX}0372"],

    # -------------------------------------------------------------------------
    # FRP SADDLE SUPPORTS (SC7x series)
    # Each code has multiple drawings — one per pipe size sub-range.
    # The 2-digit suffix (-01/-02/…) identifies the sub-range sheet.
    # Note: 2-digit suffixes are NOT stripped by _drawing_base(), so each
    # "07xx-yy" entry is a separate key in DRAWING_SIZE_RANGES below.
    # -------------------------------------------------------------------------
    "SC71":  [                              # FRP Rest (primary) — 3/4" to 68"
        f"{DRAWING_PREFIX}0701-01",         #   3/4" – 8"
        f"{DRAWING_PREFIX}0701-02",         #   10"  – 14"
        f"{DRAWING_PREFIX}0701-03",         #   16"  – 24"
        f"{DRAWING_PREFIX}0701-04",         #   26"  – 68"
    ],
    "SC72":  [                              # FRP Rest (alternative) — 3/4" to 52" (gap at 26")
        f"{DRAWING_PREFIX}0702-01",         #   3/4" – 6"
        f"{DRAWING_PREFIX}0702-02",         #   8"   – 14"
        f"{DRAWING_PREFIX}0702-03",         #   16"  – 24"
        f"{DRAWING_PREFIX}0702-04",         #   28"  – 52"
    ],
    "SC73":  [                              # FRP Guide — 3/4" to 52" (gap at 26")
        f"{DRAWING_PREFIX}0703-01",         #   3/4" – 8"
        f"{DRAWING_PREFIX}0703-02",         #   10"  – 14"
        f"{DRAWING_PREFIX}0703-03",         #   16"  – 24"
        f"{DRAWING_PREFIX}0703-04",         #   28"  – 52"
    ],
    "SC74":  [                              # FRP Sloped Shoe — 1" to 60"
        f"{DRAWING_PREFIX}0704-01",         #   1"   – 8"
        f"{DRAWING_PREFIX}0704-02",         #   10"  – 60"
    ],
}


# =============================================================================
# DRAWING SIZE RANGES
# Maps the 4-digit drawing base number to the (min_nps, max_nps) it covers.
# Used to filter drawing references so only the sheet(s) relevant to the
# selected pipe size are shown.
#
# Source: title blocks and dimension tables in QW2507-00-PE-STD-00001.pdf.
# Sheet suffixes (-001/-002) share the same range as the base drawing.
# =============================================================================

DRAWING_SIZE_RANGES = {
    # Bearing Plate
    "0321":  (0.5,  48.0),  # BP02 — all sizes

    # Wear Pad Assemblies
    "0322":  (1.5,  48.0),  # WA01
    "0323":  (2.0,  48.0),  # WA02
    "0324":  (2.0,  48.0),  # WA03

    # Pipe Shoes — standard (non-sloping)
    "0327":  (1.5,  24.0),  # SH01
    "0328":  (26.0, 48.0),  # SH02

    # Pipe Shoes — sloping / special
    "0329":  (1.5,  48.0),  # SH03  (line stop + SS/AL + temp > 400°C)
    "0330":  (1.5,   4.0),  # SH04  (sloping, 1½"–4")
    "0331":  (6.0,  48.0),  # SH05  (sloping, 6"–48")

    # Shoe Clamps — non-sloping
    "0342":  (1.5,  24.0),  # SC01
    "0343":  (1.5,  24.0),  # SC02
    "0344":  (1.5,  24.0),  # SC03
    "0345":  (1.5,  24.0),  # SC04

    # Shoe Clamps — sloping (paired with SH03–SH05)
    # Each drawing covers two size bands: 1-1/2"–4" (with SH04) and 6"–24" (with SH05/SH03).
    # Verified from drawing text: "PIPE SIZE 1-1/2" TO 4"" and "PIPE SIZE 6" TO 24"".
    "0346":  (1.5,  24.0),  # SC05  (1½"–4" with SH04; 6"–24" with SH05 — confirmed)
    "0347":  (1.5,  24.0),  # SC06  (1½"–4" with SH04; 6"–24" with SH05 — confirmed)
    "0348":  (1.5,  24.0),  # SC07  (1½"–4" with SH04; 6"–24" with SH05 — confirmed)
    "0349":  (1.5,  24.0),  # SC08  (1½"–4" with SH04; 6"–24" with SH03/SH05 — confirmed)

    # Guide Supports
    "0357":  (0.5,  48.0),  # GL01
    "0358":  (0.5,  48.0),  # GL02

    # Line Stop Supports
    "0359":  (0.5,  48.0),  # LS01
    "0360":  (0.5,   6.0),  # LS02  (up to 6")
    "0361":  (8.0,  48.0),  # LS03  (8"–48")

    # Hold Down / Guide-Hold
    "0362":  (0.5,  48.0),  # GH01
    "0363":  (0.75, 10.0),  # GH02  (¾"–10")

    # FRP Clamp Shoes (CF series — older standard drawings)
    "0369":  (2.0,  24.0),  # CF01
    "0370":  (2.0,  24.0),  # CF02
    "0371":  (2.0,  24.0),  # CF03
    "0372":  (2.0,  24.0),  # CF04 (note: drawing 0372 is actually SF01 in this PDF rev)

    # FRP Saddle Supports — SC71 (2-digit sub-range suffix, full key kept as-is)
    # Confirmed from PDF index page 7: drawing numbers JS-PE-DPS-0701-01 to 0701-04.
    # _drawing_base() strips only 3-digit suffixes, so "0701-01" is the full lookup key.
    "0701-01": (0.75,  8.0),   # SC71 sub-range 1: 3/4"–8"
    "0701-02": (10.0, 14.0),   # SC71 sub-range 2: 10"–14"
    "0701-03": (16.0, 24.0),   # SC71 sub-range 3: 16"–24"
    "0701-04": (26.0, 68.0),   # SC71 sub-range 4: 26"–68" (tool max 48")

    # FRP Saddle Supports — SC72 (gap at 26": no drawing covers that size)
    "0702-01": (0.75,  6.0),   # SC72 sub-range 1: 3/4"–6"
    "0702-02": (8.0,  14.0),   # SC72 sub-range 2: 8"–14"
    "0702-03": (16.0, 24.0),   # SC72 sub-range 3: 16"–24"
    "0702-04": (28.0, 52.0),   # SC72 sub-range 4: 28"–52"

    # FRP Saddle Guide — SC73 (gap at 26": same as SC72)
    "0703-01": (0.75,  8.0),   # SC73 sub-range 1: 3/4"–8"
    "0703-02": (10.0, 14.0),   # SC73 sub-range 2: 10"–14"
    "0703-03": (16.0, 24.0),   # SC73 sub-range 3: 16"–24"
    "0703-04": (28.0, 52.0),   # SC73 sub-range 4: 28"–52"

    # FRP Sloped Saddle — SC74
    "0704-01": (1.0,   8.0),   # SC74 sub-range 1: 1"–8"
    "0704-02": (10.0, 60.0),   # SC74 sub-range 2: 10"–60" (tool max 48")
}


def _drawing_base(ref: str) -> str:
    """Extract the 4-digit base number from a drawing reference string.

    'JS-PE-DPS-0327-001' → '0327'
    'JS-PE-DPS-0327'     → '0327'
    'JS-PE-DPS-SC71'     → 'SC71'  (FRP saddle, no size filter)
    """
    # Strip prefix
    s = ref.upper().replace("JS-PE-DPS-", "")
    # Strip sheet suffix (-001, -002, …)
    s = re.sub(r"-\d{3}$", "", s)
    return s


def _drawing_covers_nps(ref: str, nps: float) -> bool:
    """Return True if the drawing covers the given NPS."""
    base = _drawing_base(ref)
    size_range = DRAWING_SIZE_RANGES.get(base)
    if size_range is None:
        return True   # unknown range → include by default (FRP saddle codes etc.)
    min_nps, max_nps = size_range
    return min_nps <= nps <= max_nps


def _expand_code_ranges(s: str) -> str:
    """Expand shorthand range notation like SC02-SC04 into SC02/SC03/SC04.

    The support rules use compact range strings (e.g. "SC02-SC04, SC06-SC09")
    to mean "any of SC02, SC03, SC04".  Without expansion the regex below only
    sees the first and last code of each range.
    """
    def _expand(m):
        prefix, n1, n2 = m.group(1), int(m.group(2)), int(m.group(4))
        if m.group(1) == m.group(3) and n2 > n1:
            return "/".join(f"{prefix}{i:02d}" for i in range(n1, n2 + 1))
        return m.group(0)   # leave unchanged if prefixes differ or range invalid

    return re.sub(r'\b([A-Z]{2})(\d{2})-([A-Z]{2})(\d{2})\b', _expand, s)


def get_drawings(support_code: str, nps: float = None) -> list:
    """
    Return drawing reference numbers for a given support code or compound support string.

    Extracts all drawing codes (e.g. SH01, GL02, CF04) from the string using a
    regex, then looks each one up in DRAWING_INDEX.  Codes not in the index are
    silently skipped.  Results are de-duplicated and ordered by first appearance.

    Range notation like "SC02-SC04" is expanded to "SC02/SC03/SC04" before
    extraction so that all codes in the range are included.

    If *nps* is supplied, only drawings whose documented size range includes
    that NPS are returned (Improvement 1 — filter by pipe size).

    Examples:
        get_drawings("WELDED SHOE (SH01/SH05) + WEAR PAD (WA01)", nps=30)
            → ["JS-PE-DPS-0331",
               "JS-PE-DPS-0322-001", "JS-PE-DPS-0322-002"]
            (SH01/0327 excluded because it only covers 1½"–24")

        get_drawings("WELDED SHOE (SH01/SH05) + WEAR PAD (WA01)")
            → all 5 refs (unfiltered, backward-compatible)

        get_drawings("DIRECT REST") → []
    """
    if not support_code:
        return []

    # Expand range notation (e.g. "SC02-SC04" → "SC02/SC03/SC04") before parsing
    expanded = _expand_code_ranges(support_code.upper())

    # Match codes like SH01, GL02, CF04, SC71 — 2 uppercase letters + 2 digits
    codes = re.findall(r'\b([A-Z]{2}\d{2})\b', expanded)

    seen = set()
    drawings = []
    for code in codes:
        if code not in seen:
            seen.add(code)
            for ref in DRAWING_INDEX.get(code, []):
                if ref not in drawings:
                    if nps is None or _drawing_covers_nps(ref, nps):
                        drawings.append(ref)

    return drawings
