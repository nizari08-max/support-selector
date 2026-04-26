# CONTEXT — JESA Piping Support Selector

Reference document for continuing development in future sessions.

---

## Project Purpose

A web-based decision-support tool used by JESA piping engineers.  
Given five inputs (pipe size, material, heat treatment, insulation, support function) it returns:
- The correct piping support type (e.g. "WELDED SHOE (SH01) + WEAR PAD (WA01)")
- The drawing reference numbers for that support
- Applicable engineering notes
- A clickable link on each drawing chip that opens the actual drawing page from the JESA standard PDF, with the relevant pipe-size row highlighted yellow

---

## Project Structure

```
repo root/
├── app.py                          Flask web application (entry point for server)
├── selector.py                     Core selection logic — normalises inputs, runs rules lookup
├── support_rules.py                Nested dict of all support selection rules (Table 15 & 16)
├── drawing_index.py                Maps support codes → drawing reference numbers
├── pdf_service.py                  PDF extraction + NPS row highlighting (PyMuPDF)
├── main.py                         CLI version (asks questions in terminal, prints result)
├── requirements.txt                flask, gunicorn, PyMuPDF
├── Procfile                        "web: python app.py"  (Railway/Render deployment)
├── QW2507-00-PE-STD-00001.pdf      JESA Piping Support Standard Rev A (190 pages, 22.5 MB)
│
├── templates/
│   └── index.html                  Single-page HTML app (all UI in one file)
│
├── static/
│   ├── css/style.css               All styles
│   ├── js/app.js                   All frontend logic (vanilla JS, no framework)
│   └── images/
│       ├── logo_jesa.svg
│       └── supports/               SVG illustrations (one per support type)
│
└── piping_support_tool/            Mirror of root — kept in sync manually
    └── (same structure as root)
```

**Deployed file:** `app.py` at repo root (not the one in `piping_support_tool/`).  
The `piping_support_tool/` subfolder is a legacy copy that is kept in sync by manually copying changed files.

---

## How the Main Pieces Connect

```
Browser (index.html + app.js)
    │
    │  POST /api/select  {nps, material, pwht, insulation, function}
    ▼
app.py  →  select_support()  [selector.py]
                │
                ├── normalize_function / normalize_material / normalize_insulation / get_size_range
                ├── SUPPORT_RULES lookup  [support_rules.py]
                └── get_drawings(support_code, nps=nps)  [drawing_index.py]
                        └── filters refs via DRAWING_SIZE_RANGES
                │
                └── SelectionResult(support_code, drawings, notes, size_range, inputs)
    │
    │  JSON response → showResult(data) in app.js
    │
    │  User clicks drawing chip
    │  GET /api/drawing/JS-PE-DPS-0327-001?nps=8
    ▼
app.py  →  get_drawing_pdf(drawing_ref, nps)  [pdf_service.py]
                │
                ├── DRAWING_PAGES[ref]  → page index(es) in PDF
                ├── fitz.open(PDF) → copy pages → draw yellow rect on NPS text hits
                └── return PDF bytes
    │
    │  application/pdf response → browser opens in new tab
    ▼
Browser displays drawing with highlighted NPS row
```

---

## The Standard PDF

**File:** `QW2507-00-PE-STD-00001.pdf`  
**Title:** JESA Onshore Piping Support Standard, Project QW2507, Rev A  
**Pages:** 190  
**Size:** 22.5 MB

### Structure of the PDF

| Pages (1-indexed) | Content |
|---|---|
| 1–8 | Cover, revision history, scope, drawing index tables |
| 9–16 | Index pages listing all drawing numbers by family |
| 17–24 | More index pages (spring hangers, embedded plates, etc.) |
| **25–73** | **Actual engineering drawings — the pages used by pdf_service.py** |
| 74–190 | Additional support types not currently in the selector (SF, GS, UB, TR, CL, spring hangers) |

### How the drawings are stored in the PDF

Each drawing page (25–73) contains:
- **One raster image** — the engineering drawing (lines, dimensions, views). This is NOT searchable text.
- **One text layer** — dimension tables, pipe size lists, notes, support identification codes. This IS searchable via PyMuPDF `page.get_text()` and `page.search_for()`.

The text layer is what enables NPS row highlighting. The drawing number itself (e.g. `JS-PE-DPS-0327`) is often only in the raster image title block, not in the text layer — this is why `pdf_service.py` uses a hand-built page mapping dict rather than searching by drawing number.

### Drawing families used by the selector

| Code prefix | Description | Drawing numbers | Pages (0-indexed) |
|---|---|---|---|
| BP | Bearing Plate | 0321 | 24 |
| WA | Wear Pad Assembly | 0322–0324 | 25–30 |
| SH | Pipe Shoe (standard) | 0327–0328 | 31–34 |
| SH | Pipe Shoe (sloping) | 0329–0331 | 35–39 |
| SC | Shoe Clamp (non-sloping) | 0342–0345 | 50–53 |
| SC | Shoe Clamp (sloping) | 0346–0349 | 54–57 |
| GL | Guide Support | 0357–0358 | 60–62 |
| LS | Line Stop Support | 0359–0361 | 63–66 |
| GH | Hold Down / Guide-Hold | 0362–0363 | 67–68 |
| CF | FRP Clamp Shoe | 0369–0372 | 69–73 |

---

## Critical Data Formats

### 1. NPS (Nominal Pipe Size)

Stored as `float` throughout the codebase.

| Input button label | Internal float value |
|---|---|
| ½ | 0.5 |
| ¾ | 0.75 |
| 1 | 1.0 |
| 1½ | 1.5 |
| 2 … 48 | 2.0 … 48.0 (integers only above 1.5) |

**In the PDF text layer**, pipe sizes appear as: `1-1/2"`, `2"`, `30"` etc. (inch symbol is standard ASCII `"`).

### 2. Support Rules Lookup Path

`SUPPORT_RULES[function_key][size_range][material_key][pwht_key?][insulation_key]`

- `function_key`: `"rest"` | `"guide"` | `"line_stop"` | `"hold_down"`
- `size_range` for REST: `"0.5_to_1"` | `"1.5"` | `"2_to_16"` | `"18_to_24"` | `"26_to_30"` | `"32_to_48"`
- `size_range` for GUIDE/LS/HD: `"0.5_to_1"` | `"1.5_to_6"` | `"8_to_10"` | `"12_to_48"`
- `material_key`: `"cs_lt"` | `"ss_ds_sd_sa"` | `"al_ay_cn"` | `"frp"`
- `pwht_key` (CS/LT only): `"pwht"` | `"no_pwht"`
- `insulation_key`: `"uninsulated"` | `"hot_insulated"`

Leaf value: `{"support": "SH01 + WA01", "notes": [1, 3]}` or `{"support": None, "notes": []}`.

### 3. Drawing Reference String Format

`"JS-PE-DPS-XXXX-00N"` where:
- `XXXX` = 4-digit drawing number (e.g. `0327`)
- `00N` = sheet number (e.g. `001`, `002`) — omitted for single-sheet drawings

Examples: `"JS-PE-DPS-0327-001"`, `"JS-PE-DPS-0342"`, `"JS-PE-DPS-SC71"` (FRP saddle, non-standard)

### 4. Drawing Size Ranges

Stored in `DRAWING_SIZE_RANGES` in `drawing_index.py`.  
Key: 4-digit base number as string (e.g. `"0327"`).  
Value: `(min_nps: float, max_nps: float)`.

Both sheets of a multi-sheet drawing (e.g. `0327-001` and `0327-002`) share the same size range — the base number `"0327"` covers both.

### 5. `/api/select` JSON response

```json
{
  "success": true,
  "support_code": "WELDED SHOE (SH02/SH05) + WEAR PAD (WA01)",
  "drawings": ["JS-PE-DPS-0328-001", "JS-PE-DPS-0328-002", "JS-PE-DPS-0331", "JS-PE-DPS-0322-001", "JS-PE-DPS-0322-002"],
  "notes": ["Note text 1", "Note text 2"],
  "is_applicable": true,
  "image_key": "pipe_shoe",
  "size_range": "26_to_30"
}
```

`drawings` is already filtered by the selected NPS (only sheets whose documented range covers the NPS are included).

### 6. `/api/drawing/<ref>?nps=<nps>` response

Returns `application/pdf` bytes inline.  
Filename: `<ref>_<nps>in.pdf` (e.g. `JS-PE-DPS-0327-001_8in.pdf`).  
Returns HTTP 404 if ref not in `DRAWING_PAGES` or PDF file not found on server.

---

## Material Class Aliases (selector.py)

| User input | Normalised key | PWHT applies? |
|---|---|---|
| CS, LT, cladded | `cs_lt` | Yes |
| SS, DS, SD, SA | `ss_ds_sd_sa` | No |
| AL, AY, CN | `al_ay_cn` | No |
| FRP, GRP, fiberglass | `frp` | No (handled separately) |

FRP is a special case — bypasses `SUPPORT_RULES` entirely and uses hard-coded logic in `selector.py` (SC71/SC72/SC73 for rest, SC73 for guide, CF03 for line stop, N/A for hold down).

---

## Frontend State (app.js)

```javascript
let state = {
  nps:        null,    // float or null
  material:   "",      // raw dropdown value e.g. "CS"
  pwht:       false,   // boolean
  insulation: "uninsulated",  // "uninsulated" | "hot_insulated"
  fn:         null,    // "rest" | "guide" | "line_stop" | "hold_down"
};
```

`state.nps` is used directly when constructing drawing chip href URLs:  
`/api/drawing/${encodeURIComponent(dwg)}?nps=${state.nps}`

---

## Environment / Deployment

| Platform | Config file | Entry point |
|---|---|---|
| Railway | `nixpacks.toml` (in `piping_support_tool/`) | `python app.py` |
| Render | `render.yaml` (in `piping_support_tool/`) | gunicorn via Procfile |
| Local | — | `python app.py` then open `http://localhost:5000` |

**PDF location on server:** `/app/QW2507-00-PE-STD-00001.pdf` (repo root = `/app` on Railway/Render).  
Override with env var `PDF_PATH` if the file is stored elsewhere.

**Python version:** 3.7+ required (f-strings, `typing` used). Tested with 3.13.

**No database** — all data is in Python dicts in source files.
