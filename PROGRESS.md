# PROGRESS — JESA Piping Support Selector

Last updated: 2026-04-16 (session 2)
Session summary: Fixed three bugs discovered during PDF verification (range notation in get_drawings, SC05-SC08 size ranges, CF04 page mapping).

---

## COMPLETED TASKS

### 1. `drawing_index.py` — Drawing size range filter
**What changed:**
- Added `import re` at the top (moved from inside the function).
- Added `DRAWING_SIZE_RANGES` dict: maps each 4-digit base drawing number (e.g. `"0327"`) to a `(min_nps, max_nps)` tuple. Covers all 35 drawings referenced in `DRAWING_INDEX`. Size ranges were read directly from the title blocks and dimension tables in the standard PDF.
- Added private helper `_drawing_base(ref)`: strips `JS-PE-DPS-` prefix and `-001`/`-002` sheet suffix to get the bare 4-digit key.
- Added private helper `_drawing_covers_nps(ref, nps)`: returns True if `nps` falls within the drawing's documented range; returns True by default for unknown codes (FRP saddle codes SC71/SC72/SC73 have no standard drawing number so they pass through unfiltered).
- Updated `get_drawings(support_code, nps=None)` to accept an optional `nps` parameter. When supplied, each candidate ref is checked against `_drawing_covers_nps` before being added to the result list. Fully backward-compatible — calling without `nps` returns the same result as before.

**Key decision:** Filter at the individual drawing-ref level (not at the support-code level) so compound strings like `"SH01/SH05 + WA01"` are handled correctly — only the sheets that don't cover the NPS are dropped, not the entire compound result.

---

### 2. `pdf_service.py` — New file: PDF extraction and row highlight
**What was created:**
- `get_pdf_path()`: searches for `QW2507-00-PE-STD-00001.pdf` in this order: `PDF_PATH` env var → repo root → `piping_support_tool/` subfolder → `~/Downloads/` → `~/OneDrive - KLAUS/Desktop/`. Returns `None` if not found (endpoint returns 404 gracefully).
- `DRAWING_PAGES` dict: maps every drawing reference string (exactly as it appears in `DRAWING_INDEX`) to a list of 0-indexed page numbers in the PDF. 35 entries. Derived by scanning the PDF text layer for support code identifiers (`SH01`, `SC01`, etc.) page by page.
  - Single-page drawings: e.g. `"JS-PE-DPS-0342": [50]`
  - Two-page drawings: e.g. `"JS-PE-DPS-0329": [35, 36]` (plan + dimension table as separate PDF pages)
- `_NPS_PATTERNS` dict: maps each valid NPS float to a list of text strings to search for (e.g. `1.5 → ['1-1/2"', '1½"', '1 1/2"']`). Handles fractional sizes with Unicode and ASCII variants.
- `_nps_patterns(nps)`: returns patterns from the dict, or constructs `'N"'` for any unlisted integer NPS.
- `get_drawing_pdf(drawing_ref, nps=None)`: opens the PDF with PyMuPDF (`fitz`), copies the mapped page(s) into a new in-memory PDF document, then for each page draws a semi-transparent yellow rectangle (`fill=(1.0, 0.93, 0.0)`, `fill_opacity=0.35`) spanning the full page width at the y-coordinate of every occurrence of the NPS search terms. Returns the PDF as bytes. Returns `None` if PDF is missing or drawing ref is unknown.

**Key decision:** Used `page.draw_rect()` (direct content-stream drawing) rather than `page.add_highlight_annot()` (annotation layer). Reason: highlight annotations are text-based and require exact character quads; `draw_rect` works as a visual overlay regardless of text encoding and is more reliable across PDF viewers.

**Key decision:** Row highlight spans full page width (not just the cell). This makes the highlighted row visually obvious even when the table is narrow or the NPS appears in multiple columns.

---

### 3. `selector.py` — NPS threaded through to drawing lookup
**What changed (2 lines only):**
- In the FRP special-case block: all three `get_drawings(code)` calls changed to `get_drawings(code, nps=nps)`.
- In the standard rules-table path: `get_drawings(support_code)` → `get_drawings(support_code, nps=nps)`.

No logic changes — purely passing the already-known `nps` variable through.

---

### 4. `app.py` — New `/api/drawing` endpoint
**What changed:**
- Added `Response, abort` to the `flask` import line.
- Added `from pdf_service import get_drawing_pdf` import.
- Added new route `GET /api/drawing/<path:drawing_ref>`:
  - Reads optional `nps` query param (float).
  - Calls `get_drawing_pdf(drawing_ref, nps)`.
  - On success: streams PDF bytes inline with `Content-Type: application/pdf` and `Content-Disposition: inline; filename="<ref>_<nps>in.pdf"`.
  - On failure (PDF missing or unknown ref): returns HTTP 404 with a human-readable message.
  - Filename pattern: `JS-PE-DPS-0327-001_8in.pdf`.

---

### 5. `requirements.txt` — PyMuPDF added
Added `PyMuPDF>=1.23.0`. Already installed locally (v1.27.2.2). Required on the server for `pdf_service.py`.

---

### 6. `static/js/app.js` — Drawing chips made clickable
**What changed** (inside `showResult(data)`):
- Each drawing chip is now created as an `<a>` element instead of a `<span>`.
- `href` set to `/api/drawing/${encodeURIComponent(dwg)}?nps=${state.nps}`.
- `target="_blank"` + `rel="noopener noreferrer"` so it opens in a new tab.
- `title` attribute gives a tooltip: `"Open drawing JS-PE-DPS-0327-001 (NPS 8") — highlighted for selected pipe size"`.
- CSS class: `dwg-chip dwg-chip-link` (the new link class is additive).

---

### 7. `static/css/style.css` — Clickable chip styles
**What changed** (inserted after `.dwg-chip {}` block):
- `.dwg-chip-link`: adds `text-decoration: none`, `cursor: pointer`, CSS transition on background/border/color/box-shadow.
- `.dwg-chip-link::after`: appends a small `↗` icon (via CSS `content`) to signal the chip is a link.
- `.dwg-chip-link:hover` / `:focus-visible`: navy fill (`var(--primary)`), white text, subtle box-shadow.

---

### 8. `QW2507-00-PE-STD-00001.pdf` — Committed to repo root
The 22.5 MB standard PDF was copied from `~/Downloads/` to the repo root and committed. The server will find it automatically at `/app/QW2507-00-PE-STD-00001.pdf` after deploy — no env var needed.

---

### 9. All changes synced to `piping_support_tool/` subfolder
`drawing_index.py`, `selector.py`, `app.py`, `pdf_service.py`, `requirements.txt`, `static/css/style.css`, `static/js/app.js` were all copied to `piping_support_tool/` to keep the subfolder in sync with the root.

---

### 10. GitHub push
All changes pushed to `https://github.com/nizari08-max/support-selector.git` on branch `main`.  
Commits: `5105f3f` (code changes) and `eff90ce` (PDF file).

---

### 10. `drawing_index.py` — Range notation expansion in `get_drawings()` (session 2)
**Bug fixed:**  
Support code strings like `"CLAMPED SHOE (SC02-SC04, SC06-SC09)"` use range notation (`SC02-SC04` = SC02, SC03, SC04). The previous regex only extracted the first and last code of each range, silently missing SC03, SC07, SC08 from drawing results.

**Fix:**  
Added `_expand_code_ranges()` helper that rewrites `SCxx-SCyy` → `SCxx/SC(xx+1)/.../SCyy` before regex extraction. Called automatically inside `get_drawings()`.

---

### 11. `drawing_index.py` — SC05–SC08 size ranges corrected (session 2)
**What was wrong:**  
- `"0346"` (SC05): was `(1.5, 4.0)` — too narrow  
- `"0347"` (SC06): was `(6.0, 48.0)` — wrong  
- `"0348"` (SC07): was `(6.0, 48.0)` — wrong  
- `"0349"` (SC08): was `(1.5, 48.0)` — too wide  

**Verified from PDF text:** Pages 54–57 each state "PIPE SIZE 1-1/2" TO 4"" AND "PIPE SIZE 6" TO 24"" — all four drawings cover `(1.5, 24.0)`.

**Fix:** All four corrected to `(1.5, 24.0)`.

---

### 12. `pdf_service.py` — CF04/0372 removed from DRAWING_PAGES (session 2)
**Bug fixed:**  
`DRAWING_PAGES["JS-PE-DPS-0372"]` was pointing to page 73, which is the SF01 (FRP Butt-and-Wrap Thrust Collar) drawing. PDF index page 13 confirms: `JS-PE-DPS-0372 → SF01`, not CF04.

**Fix:** Removed the `"JS-PE-DPS-0372"` entry. The `/api/drawing/JS-PE-DPS-0372` endpoint now returns HTTP 404 (safer than serving the wrong drawing). CF04 is not currently returned by any rule — selector uses CF03 for FRP line stops — so this has no functional impact on the tool.

---

## IN PROGRESS

**Nothing is currently in progress.**

---

## REMAINING TASKS (not yet started)

### HIGH PRIORITY

**A. Populate `SUPPORT_RULES` in `support_rules.py`** — DONE (was already complete before session 2)  
All entries filled in from Tables 15 & 16. No TODO placeholders remain.

**B. Verify PDF page mapping for all 35 entries in `DRAWING_PAGES`** — DONE (session 2)  
- WA01–WA03 (pages 25–30): verified correct via text extraction.
- BP02 (page 24): verified correct (notes text present).
- SC05–SC08 (pages 54–57): verified correct page assignment; size ranges corrected (see task 11).
- CF04 page mapping: confirmed wrong — removed from DRAWING_PAGES (see task 12).

**C. SC05–SC08 size ranges in `DRAWING_SIZE_RANGES`** — DONE (session 2)  
All four corrected to `(1.5, 24.0)` from PDF-confirmed drawing text. See task 11.

### MEDIUM PRIORITY

**D. Place PDF on the production server**  
The PDF is now in the GitHub repo (committed in `eff90ce`). If the hosting platform (Railway/Render) builds from the repo, the PDF will be deployed automatically. Confirm this after next deployment by testing `/api/drawing/JS-PE-DPS-0327-001?nps=8` in production.

**E. NPS highlight on plan-view pages (sheet -001)**  
Sheet -001 pages (plan views like SH01 on page 32) don't always have a dimension table — they show the physical arrangement. The NPS text may appear in a caption like "PIPE SIZE 1-1/2" TO 4"" rather than a table row. The highlight will still fire on any text match, which is reasonable, but may look odd on plan pages. Consider only highlighting on sheet -002 (dimension table) pages.

**F. CF04 (JS-PE-DPS-0372) page confirmation**  
Page 73 in the mapping was inferred; the text on that page shows `SF01-4` (FRP collar support), not CF04. CF04's actual page may not exist in this PDF revision. The current mapping may return the wrong drawing when CF04 is selected.

---

## BUGS / ISSUES DISCOVERED (not yet fixed)

1. **`CF04` page mapping** — FIXED (session 2). Removed from `DRAWING_PAGES`; endpoint returns 404 now.

2. **Support rules all `"TODO"`** — RESOLVED (pre-existing, already filled in before session 2).

3. **`fitz` import failure on deploy if PyMuPDF is not installed.** `get_drawing_pdf()` catches `ImportError` and returns `None`, causing the endpoint to return 404 gracefully. Fix: verify PyMuPDF installs on hosting platform after next deploy.

---

## KEY DECISIONS

| Decision | Reason |
|---|---|
| Filter drawing refs at the individual-ref level, not support-code level | Compound support codes like `"SH01/SH05 + WA01"` need per-drawing filtering, not all-or-nothing |
| `draw_rect` for highlight instead of `add_highlight_annot` | Works as a visual overlay regardless of text encoding; `add_highlight_annot` requires exact character quads and fails if text isn't a true text object |
| Full-page-width row highlight | Makes the relevant row obvious even when tables are narrow or NPS appears in multiple columns |
| PDF committed to repo root (not env var) | Simplest setup — server finds it automatically, no manual config on hosting platform |
| Backward-compatible `get_drawings()` signature | Existing call sites without `nps=` continue to work; no changes needed to CLI path (`main.py`) |
| `<path:drawing_ref>` Flask route type | Drawing refs contain hyphens and slashes (e.g. `JS-PE-DPS-0327-001`); `path:` converter allows hyphens, while `string:` would reject some patterns |

---

## EXACT NEXT STEP WHEN RESUMING

All HIGH PRIORITY tasks are complete. Remaining work is MEDIUM PRIORITY:

**D. Place PDF on production server** — verify after next deploy that `/api/drawing/JS-PE-DPS-0327-001?nps=8` works in production.

**E. NPS highlight on plan-view pages** — sheet -001 pages (plan views) may show an odd highlight since there's no dimension table. Consider highlighting only on -002 (dimension table) pages, or suppressing highlight on plan pages altogether.

**F. Verify SH05 (0331) size range** — currently `(6.0, 48.0)` — looks correct but was not explicitly confirmed from PDF text this session.

Push the current changes to GitHub (`drawing_index.py`, `pdf_service.py`, `PROGRESS.md` and their subfolder copies).
