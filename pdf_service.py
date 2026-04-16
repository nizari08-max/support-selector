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

    # Wear Pad Assemblies
    "JS-PE-DPS-0322-001": [25],        # WA01 sheet 001 (plan view)
    "JS-PE-DPS-0322-002": [26],        # WA01 sheet 002 (notes)
    "JS-PE-DPS-0323-001": [27],        # WA02 sheet 001
    "JS-PE-DPS-0323-002": [28],        # WA02 sheet 002
    "JS-PE-DPS-0324-001": [29],        # WA03 sheet 001
    "JS-PE-DPS-0324-002": [30],        # WA03 sheet 002

    # Pipe Shoes — standard
    "JS-PE-DPS-0327-001": [31],        # SH01 sheet 001 (plan view, 1½"–24")
    "JS-PE-DPS-0327-002": [32],        # SH01 sheet 002 (dimension table)
    "JS-PE-DPS-0328-001": [33],        # SH02 sheet 001 (plan view, 26"–48")
    "JS-PE-DPS-0328-002": [34],        # SH02 sheet 002 (dimension table)

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

    # Guide Supports
    "JS-PE-DPS-0357-001": [60],        # GL01 sheet 001 (up to 18")
    "JS-PE-DPS-0357-002": [61],        # GL01 sheet 002 (up to 48", dim table)
    "JS-PE-DPS-0358":     [62],        # GL02

    # Line Stop Supports
    "JS-PE-DPS-0359-001": [63],        # LS01 sheet 001
    "JS-PE-DPS-0359-002": [64],        # LS01 sheet 002 (dim table)
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
    0.5:  ['1/2"',  '½"',  "1/2 "],
    0.75: ['3/4"',  '¾"',  "3/4 "],
    1.0:  ['1"',    "1 \""],
    1.5:  ['1-1/2"', '1½"', "1 1/2\""],
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


def _nps_patterns(nps: float) -> list[str]:
    """Return text patterns to search for in the PDF for the given NPS."""
    if nps in _NPS_PATTERNS:
        return _NPS_PATTERNS[nps]
    n = int(nps) if nps == int(nps) else nps
    return [f'{n}"']


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

    search_terms = _nps_patterns(nps) if nps is not None else []

    for page_idx in page_indices:
        if page_idx >= len(src_doc):
            continue

        # Copy source page into the output document
        out_doc.insert_pdf(src_doc, from_page=page_idx, to_page=page_idx)
        out_page = out_doc[-1]

        if not search_terms:
            continue

        page_rect = out_page.rect

        for term in search_terms:
            hits = out_page.search_for(term, quads=False)
            for hit in hits:
                # Extend the bounding box horizontally to cover the full row,
                # making the highlight span the entire table row width.
                row_rect = fitz.Rect(
                    page_rect.x0,
                    hit.y0 - 1,
                    page_rect.x1,
                    hit.y1 + 1,
                )
                # Draw a semi-transparent yellow band over the row
                out_page.draw_rect(
                    row_rect,
                    color=None,
                    fill=(1.0, 0.93, 0.0),   # #FFED00 yellow
                    fill_opacity=0.35,
                    overlay=True,
                )

    pdf_bytes = out_doc.tobytes(garbage=3, deflate=True)
    src_doc.close()
    out_doc.close()
    return pdf_bytes
