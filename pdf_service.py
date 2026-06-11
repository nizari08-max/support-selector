"""
pdf_service.py  —  PDF extraction service for JESA Piping Support Standard

Extracts a specific drawing page from QW2507-00-PE-STD-00001.pdf and
optionally highlights the row in the dimension table that corresponds to
the user-selected pipe size.

PDF location is resolved in this order:
  1. PDF_PATH environment variable
  2. Same directory as this file (project root)
  3. piping_support_tool/ subdirectory (legacy layout)
"""

import io
import os
import re
from urllib.parse import quote

from drawing_index import DRAWING_INDEX, get_drawings

# ---------------------------------------------------------------------------
# PDF path resolution
# ---------------------------------------------------------------------------

_FILENAME = "QW2507-00-PE-STD-00001.pdf"
_HERE = os.path.dirname(os.path.abspath(__file__))

_SEARCH_PATHS = [
    os.path.join(_HERE, _FILENAME),
    os.path.join(_HERE, "piping_support_tool", _FILENAME),
]


def get_pdf_path() -> str | None:
    """Return the absolute path to the standard PDF, or None if not found."""
    env = os.environ.get("PDF_PATH")
    if env and os.path.isfile(env):
        return env
    for p in _SEARCH_PATHS:
        if os.path.isfile(p):
            return p
    return None


# ---------------------------------------------------------------------------
# Drawing reference → 0-indexed PDF page numbers
#
# Derived by scanning QW2507-00-PE-STD-00001.pdf (190 pages) for support
# code text and drawing number identifiers in the text layer.
#
# Key: exactly as it appears in DRAWING_INDEX (e.g. "JS-PE-DPS-0327-001")
# Value: list of 0-indexed page numbers to include in the extracted PDF
# ---------------------------------------------------------------------------

DRAWING_PAGES: dict[str, list[int]] = {
    # Bearing Plate
    "JS-PE-DPS-0321":     [24],        # BP02

    # Wear Pad Assemblies — merged: clicking one chip opens a 2-page PDF
    "JS-PE-DPS-0322":     [25, 26],    # WA01 (plan view + notes)
    "JS-PE-DPS-0323":     [27, 28],    # WA02 (plan view + notes)
    "JS-PE-DPS-0324":     [29, 30],    # WA03 (plan view + notes)

    # Pipe Shoes — standard, merged
    "JS-PE-DPS-0327":     [31, 32],    # SH01 (plan view 1½"–24" + dimension table)
    "JS-PE-DPS-0328":     [33, 34],    # SH02 (plan view 26"–48" + dimension table)

    # Pipe Shoes — sloping (single-ref drawings spanning 2 pages each)
    "JS-PE-DPS-0329":     [35, 36],    # SH03 (sheet 001 plan + sheet 002 table)
    "JS-PE-DPS-0330":     [37, 38],    # SH04 (sheet 001 plan + sheet 002 table)
    "JS-PE-DPS-0331":     [39],        # SH05 (single page)

    # Shoe Clamp Components
    "JS-PE-DPS-0335":     [40],        # CL01
    "JS-PE-DPS-0336":     [41, 42],    # CL02
    "JS-PE-DPS-0337":     [43],        # CL03

    # Shoe Clamps — non-sloping
    "JS-PE-DPS-0342":     [50],        # SC01
    "JS-PE-DPS-0343":     [51],        # SC02
    "JS-PE-DPS-0344":     [52],        # SC03
    "JS-PE-DPS-0345":     [53],        # SC04

    # Shoe Clamps — sloping
    "JS-PE-DPS-0346":     [54],        # SC05
    "JS-PE-DPS-0347":     [55],        # SC06
    "JS-PE-DPS-0348":     [56],        # SC07
    "JS-PE-DPS-0349":     [57],        # SC08

    # Guide Supports — GL01 merged
    "JS-PE-DPS-0357":     [60, 61],    # GL01 (plan view + dimension table)
    "JS-PE-DPS-0358":     [62],        # GL02

    # Line Stop Supports — LS01 merged
    "JS-PE-DPS-0359":     [63, 64],    # LS01 (plan view + dimension table)
    "JS-PE-DPS-0360":     [65],        # LS02 (up to 6")
    "JS-PE-DPS-0361":     [66],        # LS03 (8"–48")

    # Hold Down / Guide-Hold
    "JS-PE-DPS-0362":     [67],        # GH01
    "JS-PE-DPS-0363":     [68],        # GH02

    # FRP Clamp Shoes (CF series — older standard drawings for 2"–24")
    "JS-PE-DPS-0369":     [69, 70],    # CF01 (two pages)
    "JS-PE-DPS-0370":     [71],        # CF02
    "JS-PE-DPS-0371":     [72],        # CF03

    # Isolation Pads (PR series)
    "JS-PE-DPS-0380":     [78],        # PR01 (bonded, ¾"–10")
    "JS-PE-DPS-0381":     [79],        # PR02 (welded, ¾"–10")

    # Vertical Pipe Lug Supports (WL03-WL06 only)
    "JS-PE-DPS-0386":     [84],        # WL03
    "JS-PE-DPS-0387":     [85],        # WL04
    "JS-PE-DPS-0388":     [86],        # WL05
    "JS-PE-DPS-0389":     [87],        # WL06

    # FRP Saddle Supports — SC71 (JS-PE-DPS-0701-xx)
    # Pages confirmed by text-layer SC71 keyword scan; sequential order matches PDF index.
    "JS-PE-DPS-0701-01":  [165],       # SC71: 3/4"–8"
    "JS-PE-DPS-0701-02":  [166],       # SC71: 10"–14"
    "JS-PE-DPS-0701-03":  [167],       # SC71: 16"–24"
    "JS-PE-DPS-0701-04":  [168],       # SC71: 26"–68"

    # FRP Saddle Supports — SC72 (JS-PE-DPS-0702-xx)  [gap at 26": no drawing]
    "JS-PE-DPS-0702-01":  [169],       # SC72: 3/4"–6"
    "JS-PE-DPS-0702-02":  [170],       # SC72: 8"–14"
    "JS-PE-DPS-0702-03":  [171],       # SC72: 16"–24"
    "JS-PE-DPS-0702-04":  [172],       # SC72: 28"–52"

    # FRP Saddle Guide — SC73 (JS-PE-DPS-0703-xx)  [gap at 26": no drawing]
    # Page 176 text layer shows "SC73 - 28 - L", confirming it is the 28"–52" sheet.
    "JS-PE-DPS-0703-01":  [173],       # SC73: 3/4"–8"
    "JS-PE-DPS-0703-02":  [174],       # SC73: 10"–14"
    "JS-PE-DPS-0703-03":  [175],       # SC73: 16"–24"
    "JS-PE-DPS-0703-04":  [176],       # SC73: 28"–52"

    # FRP Sloped Saddle — SC74 (JS-PE-DPS-0704-xx)
    "JS-PE-DPS-0704-01":  [177],       # SC74: 1"–8"
    "JS-PE-DPS-0704-02":  [178],       # SC74: 10"–60"

    # FRP Riser Clamp Supports — RC71/RC72/RC73
    "JS-PE-DPS-0707-01":  [181],       # RC71: 3/4"–4"
    "JS-PE-DPS-0707-02":  [182],       # RC71: 6"–10"
    "JS-PE-DPS-0707-03":  [183],       # RC71: 12"–80"
    "JS-PE-DPS-0708-01":  [184],       # RC72: 3/4"–4"
    "JS-PE-DPS-0708-02":  [185],       # RC72: 6"–10"
    "JS-PE-DPS-0708-03":  [186],       # RC72: 12"–80"
    "JS-PE-DPS-0709-01":  [187],       # RC73: 3/4"–4"
    "JS-PE-DPS-0709-02":  [188],       # RC73: 6"–10"
    "JS-PE-DPS-0709-03":  [189],       # RC73: 12"–80"

    # Flange Frame Supports (FF01–FF06) — REST support at a pipe flange
    # Pages confirmed by searching the PDF text layer for "FF01"–"FF06".
    "JS-PE-DPS-0417":     [111],       # FF01 CL 150 — 1"–24"
    "JS-PE-DPS-0418":     [112],       # FF02 CL 300 — 1"–24"
    "JS-PE-DPS-0419":     [113],       # FF03 CL 600 — 2"–16"
    "JS-PE-DPS-0420":     [114],       # FF04 CL 900 — 2"–16"
    "JS-PE-DPS-0421":     [115],       # FF05 CL 1500 — 2"–16"
    "JS-PE-DPS-0422":     [116],       # FF06 CL 2500 — 2"–12"

    # FRP Flanged Valve Holder (FF71) — REST support for FRP piping
    # Page confirmed by searching the PDF text layer for "FF71".
    "JS-PE-DPS-0705":     [179],       # FF71 — 1"–18"
}


# ---------------------------------------------------------------------------
# NPS → text search patterns
#
# Returns the strings to look for in the PDF text layer to find the row
# that corresponds to the selected pipe size.
# ---------------------------------------------------------------------------

_NPS_PATTERNS: dict[float, list[str]] = {
    # Fractional and decimal variants cover different drawings in this standard.
    # Some pages (e.g. PR02 / JS-PE-DPS-0381) use "0.75"" and "1.5"" instead of
    # the fractional "3/4"" and "1-1/2"" forms.
    0.5:  ['1/2"',  '½"',  '0.5"',  "1/2 "],
    0.75: ['3/4"',  '¾"',  '0.75"', "3/4 "],
    1.0:  ['1"',    "1 \""],
    # '1/2"'  catches drawings that split "1 1/2"" into two words (PR01/PR02).
    # '11/2"' catches FRP saddle drawings (SC71-SC74) where the dash is lost.
    1.5:  ['1-1/2"', '1½"', '1.5"', "1 1/2\"", '11/2"', '1/2"'],
    2.0:  ['2"',    "2 \""],
    3.0:  ['3"',    "3 \""],
    4.0:  ['4"',    "4 \""],
    6.0:  ['6"',    "6 \""],
    8.0:  ['8"',    "8 \""],
    10.0: ['10"'],
    12.0: ['12"'],
    14.0: ['14"'],
    16.0: ['16"'],
    18.0: ['18"'],
    20.0: ['20"'],
    22.0: ['22"'],
    24.0: ['24"'],
    26.0: ['26"'],
    28.0: ['28"'],
    30.0: ['30"'],
    32.0: ['32"'],
    36.0: ['36"'],
    40.0: ['40"'],
    42.0: ['42"'],
    48.0: ['48"'],
}

# NPS (inches) → DN (mm) — used to search metric labels in the dimension table first
_NPS_TO_DN: dict[float, int] = {
    0.5:   15,
    0.75:  20,
    1.0:   25,
    1.5:   40,
    2.0:   50,
    3.0:   80,
    4.0:  100,
    6.0:  150,
    8.0:  200,
    10.0: 250,
    12.0: 300,
    14.0: 350,
    16.0: 400,
    18.0: 450,
    20.0: 500,
    22.0: 550,
    24.0: 600,
    26.0: 650,
    28.0: 700,
    30.0: 750,
    32.0: 800,
    36.0: 900,
    40.0: 1000,
    42.0: 1050,
    48.0: 1200,
}

_CLAMPED_SHOE_REFS = {
    "JS-PE-DPS-0342",
    "JS-PE-DPS-0343",
    "JS-PE-DPS-0344",
    "JS-PE-DPS-0345",
    "JS-PE-DPS-0346",
    "JS-PE-DPS-0347",
    "JS-PE-DPS-0348",
    "JS-PE-DPS-0349",
}

_WL_COLUMN_HIGHLIGHT_REFS = {
    "JS-PE-DPS-0386",
    "JS-PE-DPS-0387",
    "JS-PE-DPS-0388",
    "JS-PE-DPS-0389",
}


def _nps_patterns(nps: float) -> list[str]:
    """Return text patterns to search for in the PDF for the given NPS."""
    if nps in _NPS_PATTERNS:
        return _NPS_PATTERNS[nps]
    n = int(nps) if nps == int(nps) else nps
    return [f'{n}"']


def _find_row_rect(page, nps: float):
    """
    Locate the dimension-table row for *nps* on a rotation=270 page and return
    a fitz.Rect that covers only that row, constrained to the table borders.

    Coordinate-space note (rotation=270 pages):
      What appears as a horizontal table row visually is a vertical x-stripe in
      coordinate space.  All pipe-size labels share roughly the same y (~157 pt)
      but each has a unique x position.  The returned rect is therefore:
          Rect(hit.x0 - 1, table_y0, hit.x1 + 1, table_y1)
      where table_y0/table_y1 are the table's visual left/right borders expressed
      as y-values in coordinate space.

    Search order: NPS imperial patterns first (e.g. '1-1/2"', '0.75"') then DN
    metric value as fallback.  Every hit is verified against the page word list
    to ensure it is an exact word match rather than a substring of a longer token
    (e.g. '8"' inside '18"', or '40' inside '400').
    """
    import fitz

    # NPS patterns first; DN as fallback only
    nps_terms = _nps_patterns(nps)
    dn = _NPS_TO_DN.get(nps)
    dn_terms = [str(dn)] if dn is not None else []
    search_terms = nps_terms + dn_terms

    page_words = None   # lazy-loaded once and reused
    best = None

    for term in search_terms:
        hits = page.search_for(term, quads=False)
        if not hits:
            continue

        # Verify every hit is an exact word match — not a substring of a longer
        # word.  On rotation=270 pages, substring matches start at a y-offset
        # within the containing word, so their y0 lands >3 pts from the word's
        # y0, causing this check to reject them.  This handles e.g.:
        #   '8"'  matching inside '18"', '28"'
        #   '40'  matching inside '400', '40.0'
        if page_words is None:
            page_words = page.get_text("words")
        hits = [h for h in hits
                if any(abs(w[0] - h.x0) < 3 and abs(w[1] - h.y0) < 3
                       and w[4] == term
                       for w in page_words)]
        if not hits:
            continue

        # Pick the leftmost hit (smallest x0) — that is the pipe-size column
        best = min(hits, key=lambda r: r.x0)
        break

    if best is None:
        return None

    # ---- Determine table y-bounds (visual left/right borders in coord space) ----
    # table_y0: look for the column-header row.  The match must be within 200 pts
    # of the pipe-size hit to avoid picking up labels in the drawing title block
    # (e.g. SC71 has "PIPE SIZE" at x=697 in its title block, far from the table
    # at x=422; "NB" at x=437 is the real header).
    table_y0 = None
    for anchor in ("PIPE SIZE", "NPS", "NB", "DN"):
        ah = page.search_for(anchor)
        near = [h for h in ah if abs(h.x0 - best.x0) <= 200]
        if near:
            table_y0 = min(h.y0 for h in near) - 3
            break
    if table_y0 is None:
        table_y0 = best.y0 - 5

    # table_y1: bounding box of words in the table's x-band.
    # x_lo = hit.x0 - 15 stays within the table; the notes section on all known
    # drawing pages sits at x values >15 pts below (smaller x) than the last row.
    if page_words is None:
        page_words = page.get_text("words")
    x_lo = best.x0 - 15
    x_hi = best.x0 + 80   # include column headers sitting just right of the data
    band = [w for w in page_words if x_lo <= w[0] <= x_hi]
    table_y1 = (max(w[3] for w in band) + 3) if band else page.rect.y1

    # Guard: ensure valid (non-inverted) rect
    if table_y0 > table_y1:
        table_y0, table_y1 = table_y1, table_y0

    return fitz.Rect(best.x0 - 1, table_y0, best.x1 + 1, table_y1)


def _find_ff71_row_rect(page, nps: float):
    """
    Locate the FF71 table row.

    JS-PE-DPS-0705 uses bare NPS labels in the text layer (for example
    "10" and "18", without inch marks) and does not expose the DN fallback
    values used by the generic finder.  The dimension table size row sits in a
    tight band near the "NB" header, so exact word matching in that band avoids
    false matches from notes and the title block.
    """
    import fitz

    nps_label = f"{nps:g}"
    page_words = page.get_text("words")
    size_words = [
        w for w in page_words
        if 300 <= w[0] <= 445
        and 306 <= w[1] <= 322
        and w[4] == nps_label
    ]
    if not size_words:
        return None

    best = min(size_words, key=lambda w: w[0])
    x0, _y0, x1, _y1, *_ = best

    header_words = [
        w for w in page_words
        if 440 <= w[0] <= 458
        and 306 <= w[1] <= 324
        and w[4] in {"NB", "NPS", "DN"}
    ]
    table_y0 = (min(w[1] for w in header_words) - 4) if header_words else 306

    x_lo = x0 - 2
    x_hi = x1 + 2
    column_words = [w for w in page_words if x_lo <= w[0] <= x_hi and 306 <= w[1] <= 375]
    table_y1 = (max(w[3] for w in column_words) + 3) if column_words else 372

    return fitz.Rect(x0 - 1, table_y0, x1 + 1, table_y1)


def _find_wl_column_rect(page, nps: float):
    """
    Locate the selected size column in WL03-WL06 tables.

    WL dimension/load tables are arranged visually as columns by pipe size.
    In the rotated PDF coordinate space, those visual columns correspond to
    narrow y-bands spanning the DN/NPS/R/A/B/LOAD rows.
    """
    import fitz

    words = page.get_text("words")
    dn = _NPS_TO_DN.get(nps)
    if dn is None:
        return None

    dn_header = [
        w for w in words
        if w[4] == "DN" and 620 <= w[0] <= 690 and 90 <= w[1] <= 125
    ]
    if not dn_header:
        return None

    header_x0 = min(w[0] for w in dn_header) - 10
    header_x1 = max(w[2] for w in dn_header) + 10
    dn_words = [
        w for w in words
        if header_x0 <= w[0] <= header_x1
        and 125 <= w[1] <= 485
        and w[4] == str(dn)
    ]
    if not dn_words:
        return None

    target = min(dn_words, key=lambda w: abs(w[0] - dn_header[0][0]))
    target_center = (target[1] + target[3]) / 2

    size_centers = sorted(
        (w[1] + w[3]) / 2
        for w in words
        if header_x0 <= w[0] <= header_x1
        and 125 <= w[1] <= 485
        and re.fullmatch(r"\d+", w[4])
    )
    size_centers = [c for i, c in enumerate(size_centers) if i == 0 or abs(c - size_centers[i - 1]) > 2]
    try:
        idx = min(range(len(size_centers)), key=lambda i: abs(size_centers[i] - target_center))
    except ValueError:
        return None

    prev_center = size_centers[idx - 1] if idx > 0 else None
    next_center = size_centers[idx + 1] if idx + 1 < len(size_centers) else None
    y0 = ((prev_center + target_center) / 2) if prev_center is not None else target_center - 10
    y1 = ((next_center + target_center) / 2) if next_center is not None else target_center + 10

    column_words = [
        w for w in words
        if 560 <= w[0] <= 690
        and y0 <= ((w[1] + w[3]) / 2) <= y1
    ]
    if not column_words:
        return None

    x0 = min(w[0] for w in column_words) - 2
    x1 = max(w[2] for w in column_words) + 2
    return fitz.Rect(x0, y0 - 1, x1, y1 + 1)


def _highlight_mode_for_ref(ref_upper: str) -> str:
    if ref_upper in _WL_COLUMN_HIGHLIGHT_REFS:
        return "column"
    if ref_upper == "JS-PE-DPS-0705":
        return "ff71_row"
    return "row"


def _highlight_rect_for_ref(page, ref_upper: str, nps: float):
    mode = _highlight_mode_for_ref(ref_upper)
    if mode == "column":
        return _find_wl_column_rect(page, nps)
    if mode == "ff71_row":
        return _find_ff71_row_rect(page, nps)
    return _find_row_rect(page, nps)


def _drawing_link_uri(drawing_ref: str, nps: float | None, base_url: str | None) -> str:
    uri = f"/drawing-link/{quote(drawing_ref, safe='')}"
    if nps is not None:
        nps_label = f"{nps:g}"
        uri = f"{uri}?nps={quote(nps_label)}"
    if base_url:
        uri = f"{base_url.rstrip('/')}{uri}"
    return uri


def _add_reference_links(page, source_ref: str, nps: float | None, base_url: str | None) -> None:
    """Add URI links to known support-code references in clamped shoe drawings."""
    import fitz

    for code in DRAWING_INDEX:
        refs = get_drawings(code, nps=nps)
        if not refs:
            continue

        target_ref = refs[0]
        if target_ref.upper() == source_ref.upper():
            continue

        for rect in page.search_for(code, quads=False):
            page.draw_rect(
                rect + (-1, -1, 1, 1),
                color=None,
                fill=(1.0, 0.65, 0.0),
                fill_opacity=0.28,
                overlay=False,
            )
            page.insert_link({
                "kind": fitz.LINK_URI,
                "from": rect,
                "uri": _drawing_link_uri(target_ref, nps, base_url),
            })


# ---------------------------------------------------------------------------
# Core extraction function
# ---------------------------------------------------------------------------

def get_drawing_pdf(
    drawing_ref: str,
    nps: float | None = None,
    base_url: str | None = None,
) -> bytes | None:
    """
    Extract the drawing page(s) for *drawing_ref* from the standard PDF and
    return the result as PDF bytes.

    If *nps* is supplied, each occurrence of that pipe size in the text layer
    is highlighted yellow so the engineer can immediately locate the relevant
    row in the dimension table.

    Returns None if:
      • The standard PDF cannot be located
      • *drawing_ref* is not mapped to any known page
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return None

    pdf_path = get_pdf_path()
    if pdf_path is None:
        return None

    ref_upper = drawing_ref.upper()
    page_indices = DRAWING_PAGES.get(ref_upper)
    if not page_indices:
        return None

    src_doc = fitz.open(pdf_path)
    out_doc = fitz.open()

    for page_idx in page_indices:
        if page_idx >= len(src_doc):
            continue

        # Copy source page into the output document
        out_doc.insert_pdf(src_doc, from_page=page_idx, to_page=page_idx)
        out_page = out_doc[-1]

        if nps is not None:
            # Drawing pages have rotation=270: visual rows are x-stripes in
            # coordinate space.  _find_row_rect() returns the correct x-band.
            row_rect = _highlight_rect_for_ref(out_page, ref_upper, nps)
            if row_rect:
                out_page.draw_rect(
                    row_rect,
                    color=None,
                    fill=(1.0, 0.93, 0.0),   # #FFED00 yellow
                    fill_opacity=0.40,
                    overlay=True,
                )

        if ref_upper in _CLAMPED_SHOE_REFS:
            _add_reference_links(out_page, ref_upper, nps, base_url)

    pdf_bytes = out_doc.tobytes(garbage=3, deflate=True)
    src_doc.close()
    out_doc.close()
    return pdf_bytes
