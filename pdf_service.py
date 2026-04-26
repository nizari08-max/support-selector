"""
pdf_service.py  —  PDF extraction service for JESA Piping Support Standard

Extracts a specific drawing page from QW2507-00-PE-STD-00001.pdf and
optionally highlights the row in the dimension table that corresponds to
the user-selected pipe size.

PDF location is resolved in this order:
  1. PDF_PATH environment variable
  2. Same directory as this file (QW2507-00-PE-STD-00001.pdf)
  3. User Downloads folder
"""

import io
import os
import re

# ---------------------------------------------------------------------------
# PDF path resolution
# ---------------------------------------------------------------------------

_FILENAME = "QW2507-00-PE-STD-00001.pdf"
_HERE = os.path.dirname(os.path.abspath(__file__))

_SEARCH_PATHS = [
    os.path.join(_HERE, _FILENAME),
    os.path.join(_HERE, "piping_support_tool", _FILENAME),
    os.path.expanduser(f"~/Downloads/{_FILENAME}"),
    os.path.expanduser(f"~/OneDrive - KLAUS/Desktop/{_FILENAME}"),
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
    # CF04 / JS-PE-DPS-0372 omitted: PDF index confirms 0372 = SF01 (FRP Thrust Collar), not CF04

    # Isolation Pads (PR series)
    "JS-PE-DPS-0380":     [78],        # PR01 (bonded, ¾"–10")
    "JS-PE-DPS-0381":     [79],        # PR02 (welded, ¾"–10")

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


# ---------------------------------------------------------------------------
# Core extraction function
# ---------------------------------------------------------------------------

def get_drawing_pdf(drawing_ref: str, nps: float | None = None) -> bytes | None:
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

        if nps is None:
            continue

        # Drawing pages have rotation=270: visual rows are x-stripes in
        # coordinate space.  _find_row_rect() returns the correct x-band.
        row_rect = _find_row_rect(out_page, nps)
        if row_rect:
            out_page.draw_rect(
                row_rect,
                color=None,
                fill=(1.0, 0.93, 0.0),   # #FFED00 yellow
                fill_opacity=0.40,
                overlay=True,
            )

    pdf_bytes = out_doc.tobytes(garbage=3, deflate=True)
    src_doc.close()
    out_doc.close()
    return pdf_bytes
