# CONTEXT — JESA Piping Engineering Tools Platform

Reference document for AI handoffs and future development sessions.  
**Last updated:** 2026-06-11 | **Test count:** 502 passing

> For agent onboarding, read alongside `CODEX_HANDOFF.md` (current state + remaining work),
> `DESIGN_DECISIONS.md` (settled decisions — do not relitigate), and `PROJECT_SNAPSHOT.md`
> (1-page quick start).

---

## Project Purpose

A web-based decision-support tool for JESA piping engineers.  
Given pipe parameters it returns the correct support type, drawing references, and engineering notes
per JESA Piping Support Standard Rev A (QW2507-00-PE-STD-00001, 190 pages).

---

## Product Vision

**What the platform is today.** A **Piping Engineering Tools Platform** — a single governed
workspace that contains multiple engineering modules (Support Selector, Span Calculator, Rack
Calculator + DXF, Reference Tables) behind a shared application shell (top bar + left capability
rail + `⌘K` command palette). It presents as a professional engineering instrument: every result is
a stamped, traceable "sheet," every recommendation resolves to a governing clause/table/drawing, and
the tools are framed as a governed collection of independent engineering modules, not an active
connected line workflow.

**How it evolved.** It began as a single-purpose **Pipe Support Selector** (five inputs → one
support type). Span and Rack calculators, DXF export, and a Reference library were added over time.
A UI redesign then reframed the whole thing from "a Support Selector with extra pages" into a
**platform with a Workspace Home**, a global capability rail, and a consistent shell across all five
pages. An invented product name ("DATUM") was trialed and then **removed** from the UI — it had no
meaning to end users — leaving the product to present purely as a **JESA-endorsed engineering
platform**. (DATUM survives only as internal, non-user-visible code names — see
`DESIGN_DECISIONS.md`.)

**Long-term direction.** The shared **Line object** / cross-tool workflow is paused and remains
gated. The current product direction is a professional collection of independent piping engineering
tools under one governed platform. Future scaling may add more support families (vessel clips,
spring hangers), an in-context drawing viewer, and richer Reference content.
The platform stays an *instrument, not a brochure* — credibility comes from standards traceability,
not marketing.

---

## Current Modules

| Module | Route | Purpose |
|---|---|---|
| **Workspace Home** | `/` | Operational launcher: tool choice band, available engineering tools, and a Standards & Traceability register. |
| **Support Selector** | `/support-selector` | Core engine. Five inputs (NPS, material, PWHT, insulation, function) + flange/vertical sub-flows → correct support type, drawing refs, and engineering notes per Tables 15 & 16. |
| **Span Calculator** | `/span` | Computes maximum allowable support span for a line (per KS-PE-SPC-0073) and returns a pass/used-span result. |
| **Rack Calculator** | `/rack-calculator` | Pipe rack width/spacing math → true-scale arrangement schematic (SVG) with centered spare bay, dimensions, and a pipe schedule. |
| **DXF Generation** | `/rack-calculator/dxf` | Exports the approved rack geometry to a designer-ready DXF arrangement drawing (mm modelspace, CAD layers). Not a separate page — an export action of the Rack Calculator. |
| **Reference Tables** | `/reference` | Governing handbook: assumptions, formulae, conversions, span tables, and material codes. The credibility/source-of-truth surface tools cite into. |

---

## Approved Product Philosophy

These are **settled** product decisions. Do not relitigate them (see `DESIGN_DECISIONS.md`).

- **Engineering-first platform.** This is a professional engineering instrument for stress/piping
  engineers — not a consumer SaaS app, not a marketing site. Authority and precision over polish.
- **Tool-hub experience.** The four live tools are communicated as independent engineering modules
  in one governed platform. They share standards, visual language, and reference context without
  implying automatic data carryover.
- **Governed engineering decisions.** Every recommendation resolves to a governing clause, table,
  and drawing. Results are framed as review-ready/stamped, never improvised.
- **Standards & traceability are the credibility layer.** The governing document codes
  (QW2507-00-PE-STD-00001, Tables 15 & 16, KS-PE-SPC-0073) carry the trust — not big logos or
  marketing copy. Traceability is surfaced as a first-class panel.
- **Reliability & consistency.** Deterministic engine, 502 passing tests, no behavior change without
  explicit approval. "Engineering decisions you can stand behind."
- **Professional engineering software direction.** Visual references are Bentley/AVEVA/Hexagon
  (authority), Linear (keyboard velocity), Stripe/Notion (typographic discipline) — never
  startup/marketing aesthetics.

---

## Design Philosophy

These are **settled** visual/UX decisions. Do not relitigate them (see `DESIGN_DECISIONS.md`).

- **JESA-endorsed platform.** JESA branding signals **endorsement/authority**, not decoration. It
  appears in controlled spots only (top-bar lockup, title-block/seal strips, footer) and uses the
  reserved `--authority` token — **never** as an interactive color and never as a hero watermark.
- **Engineering-focused visual language.** A drafting/title-block aesthetic: result "sheets," mono
  numerics (JetBrains Mono, tabular figures), Saira Semi Condensed for display headings, Inter for
  body. Codes/numbers always read like a drawing.
- **Industrial atmosphere, not marketing.** The Workspace Home hero uses a desaturated plant photo
  as **subtle atmosphere** behind navy scrims + a faint blueprint grid — the *message* stays
  primary. No stock-photo marketing heroes elsewhere.
- **Piping engineering identity within seconds.** Drafting linework, rack/section motifs, dimension
  lines, and crop-mark framing communicate "piping engineering" immediately.
- **Blueprint / grid treatment.** A low-opacity blueprint grid is the recurring "drafting board"
  base layer for the home and empty states.
- **No marketing-style SaaS approach.** No gradient marketing heroes, no playful consumer softness,
  as little hero text as possible. Confident, concise, authoritative.
- **One coherent interactive accent.** `--datum` (teal) is the single interactive/active/live color;
  `--annotation` (amber) is for warnings/dimensions-of-interest; verdicts use pass/fail tokens.
  ~85% of any screen is neutral bg/panel/ink. No hardcoded hex outside the token layer.
- **Dual theme is mandatory.** Light ("vellum") + dark ("film") are both first-class and fully
  token-driven via `:root` / `[data-theme="dark"]`.

---

## Project Structure

```
repo root/
├── app.py                          Flask web app + routes
├── selector.py                     Core selection logic (select_support, _select_flange_support)
├── support_rules.py                Nested dict — Tables 15 & 16 selection rules
├── drawing_index.py                Support code → drawing refs; DRAWING_SIZE_RANGES NPS filter
├── note_refinement.py              Conditional engineering-note question flow
├── material_classes.py             MPMS piping class → span material (single source of truth)
├── pdf_service.py                  Drawing extraction + NPS row highlighting (PyMuPDF)
├── span_calculator.py              Support span calculator
├── rack_calculator.py              Pipe rack width/spacing math (formulas only)
├── rack_geometry.py                calculate_rack() output -> true-scale (mm) geometry model
├── rack_diagram.py                 Rack geometry model -> SVG (px scaling, two-scale symbol sizing)
├── rack_dxf.py                     Rack geometry model -> DXF arrangement drawing (mm modelspace)
├── pipe_flange_data.py             DN sizes and ASME flange rating tables
├── structural_profiles.py          Eurocode column profile widths (HEA/HEB/HEM/IPE)
├── requirements.txt                flask, gunicorn, PyMuPDF, python-dotenv, ezdxf
├── Procfile                        "web: python app.py"
├── run_local.bat                   Windows double-click launcher
├── LOCAL_RUN.md                    Local setup and troubleshooting
├── QW2507-00-PE-STD-00001.pdf      JESA Piping Support Standard Rev A
│
├── templates/
│   ├── landing.html                Workspace Home (/ — module launcher, capabilities, standards, roadmap)
│   ├── index.html                  Support selector UI (/support-selector)
│   ├── span_calculator.html
│   ├── rack_calculator.html
│   ├── reference.html              Span reference tables & lookups
│   ├── _shell_open.html            App shell: slim top bar + opens .workspace/.workspace-main
│   ├── _rail.html                  Global capability rail (Selection/Verification/Arrangement/Reference)
│   ├── _shell_close.html           Closes the shell + renders the footer
│   ├── _navbar.html                Legacy top bar — retired (no longer included by any page)
│   ├── _footer.html                Shared footer (incl. author credit)
│   └── _theme_toggle_script.html   Pre-render theme restore (flash prevention)
│
├── static/
│   ├── css/style.css               Tokens, app shell, workspace home, drawing-sheet/result-sheet
│   ├── js/app.js                   All frontend logic (vanilla JS) — NOT edited for visual changes
│   └── images/supports/            SVG illustrations per support type
│
└── tests/
    ├── test_selector.py            selector, drawing, flange, and PDF tests
    ├── test_span.py                support span calculator tests
    ├── test_rack.py                pipe rack calculator (math) tests
    ├── test_rack_geometry.py       rack geometry model + SVG schematic tests
    └── test_rack_dxf.py            rack DXF export tests
```

**Note:** `piping_support_tool/` subfolder is a legacy mirror — the active code is always at root.

---

## Architecture: How the Pieces Connect

```
Browser (index.html + app.js)
    │
    │  POST /api/select  {nps, material, pwht, insulation, function,
    │                     is_flange, flange_class, pipe_orientation,
    │                     vertical_restraint, refinements, piping_class}
    ▼
app.py  →  select_support()  [selector.py]
                │
                ├── normalize_function / normalize_material / normalize_insulation / get_size_range
                │
                ├── if REST + is_flange → _select_flange_support()
                │       ├── FRP (any flange type) → FF71 (1"–18")
                │       └── metallic materials   → FF01–FF06 by pressure class
                │
                ├── if pipe_orientation=vertical → WL03–WL06 branch
                │       ├── bare + sliding → WL03
                │       ├── bare + fixed → WL04
                │       ├── insulated + sliding → WL05
                │       └── insulated + fixed → WL06
                │
                ├── FRP special-case path (non-flange)
                │       ├── REST  → SC71/SC72 or SC71-only (NPS 26")
                │       ├── GUIDE → SC73 (N/A at NPS 26")
                │       ├── LINE STOP → CF03 + Note 6 deviation warning
                │       └── HOLD DOWN → N/A
                │
                ├── SUPPORT_RULES[fn][size_range][material][pwht?][insulation]
                │       └── {support: "...", notes: [...]}
                │
                └── apply_refinements() → get_drawings(code, nps) → SelectionResult
    │
    │  JSON response → showResult(data)
    │
    │  User clicks drawing chip
    │  GET /api/drawing/JS-PE-DPS-0327?nps=8
    ▼
app.py  →  get_drawing_pdf(ref, nps)  [pdf_service.py]
                ├── DRAWING_PAGES[ref] → page index in PDF
                ├── fitz.open(PDF) → extract page → highlight NPS text hits (yellow rect)
                └── return PDF bytes (application/pdf)
```

---

## The Standard PDF

**File:** `QW2507-00-PE-STD-00001.pdf` | 190 pages | 22.5 MB

| Pages (1-indexed) | Content |
|---|---|
| 1–8 | Cover, revision history, scope, drawing index tables |
| 9–24 | Index pages — all drawing numbers by family |
| 25–73 | Engineering drawings used by the selector |
| 74–190 | Additional types not yet in selector (SF, GS, UB, TR, spring hangers, vessel clips) |

Each drawing page has: a raster image (the drawing) + a text layer (searchable via PyMuPDF).  
Drawing numbers in the title block are often raster-only — `pdf_service.py` uses `DRAWING_PAGES`,
a hand-built dict mapping drawing reference → PDF page index.

### Drawing families in the selector

| Code | Description | Drawing numbers | NPS range |
|---|---|---|---|
| BP02 | Bearing Plate | 0321 | ½"–48" |
| WA01–03 | Wear Pad Assemblies | 0322–0324 | 1½"–48" |
| SH01–05 | Pipe Shoes | 0327–0331 | 1½"–48" |
| SC01–08 | Shoe Clamps / Saddle | 0342–0349 | 1½"–24" |
| GL01–02 | Guide Supports | 0357–0358 | ½"–48" |
| LS01–03 | Line Stop Supports | 0359–0361 | ½"–48" |
| GH01–02 | Hold Down / Guide-Hold | 0362–0363 | ½"–48" |
| PR01–02 | Isolation Pads | 0380–0381 | ¾"–48" |
| CF01–03 | FRP Clamp Shoes | 0369–0371 | 2"–24" |
| SC71–74 | FRP Saddle Supports | 0701–0704 (-01 to -04) | ¾"–68" |
| FF01–FF06 | Metallic Flange Frame / flanged valve support | 0417–0422 | 1"–24" (class-dependent) |
| FF71 | FRP Flanged Valve Holder | 0705 | 1"–18" |
| WL03–WL06 | Vertical Pipe Lug Supports | 0386–0389 | 1"–24" |

**FF01–FF06 NPS limits by pressure class:**

| Code | Class | Min NPS | Max NPS |
|---|---|---|---|
| FF01 | CL 150 | 1" | 24" |
| FF02 | CL 300 | 1" | 24" |
| FF03 | CL 600 | 2" | 16" |
| FF04 | CL 900 | 2" | 16" |
| FF05 | CL 1500 | 2" | 16" |
| FF06 | CL 2500 | 2" | 12" |

**FF drawing pages confirmed and added to `DRAWING_PAGES` in `pdf_service.py`.**
FF01 (p111), FF02 (p112), FF03 (p113), FF04 (p114), FF05 (p115), FF06 (p116), FF71 (p179) — all 0-indexed.

**FF PDF highlighting status:** complete. FF01–FF06 continue to use the generic rotation-table x-band row finder. FF71 / `JS-PE-DPS-0705` has a dedicated row finder because its PDF text layer exposes bare NPS labels such as `10` and `18` instead of inch-marked labels like `10"`.

**WL PDF highlighting status:** complete for Phase 2.2A. WL03–WL06 / `JS-PE-DPS-0386`–`0389` use a dedicated column-highlighting path because the size data is arranged by NPS columns. Standard supports and FF drawings keep their existing row-highlighting behavior.

**WL referenced drawings:** result payloads include secondary clickable references where the WL drawing points to another standard drawing:
- WL03 / 0386 → related 0387
- WL04 / 0387 → related 0386
- WL05 / 0388 → related 0386
- WL06 / 0389 → related 0386 and 0388

---

## Critical Data Formats

### NPS
Float throughout. ½=0.5, ¾=0.75, 1=1.0, 1½=1.5, then integer floats 2.0–48.0.  
In PDF text layer: `1-1/2"`, `2"`, `30"` (standard ASCII inch symbol).

### Support rules lookup path
```
SUPPORT_RULES[function_key][size_range][material_key][pwht_key?][insulation_key]
→ {"support": "SH01 + WA01", "notes": [1, 3]}   # or {"support": None, "notes": []}
```
- `function_key`: `"rest"` | `"guide"` | `"line_stop"` | `"hold_down"`
- `size_range` REST: `"0.5_to_1"` | `"1.5"` | `"2_to_16"` | `"18_to_24"` | `"26_to_30"` | `"32_to_48"`
- `size_range` GUIDE/LS/HD: `"0.5_to_1"` | `"1.5_to_6"` | `"8_to_10"` | `"12_to_48"`
- `material_key`: `"cs_lt"` | `"ss_ds_sd_sa"` | `"al_ay_cn"` | `"frp"`
- `pwht_key` (CS/LT only): `"pwht"` | `"no_pwht"`
- `insulation_key`: `"uninsulated"` | `"hot_insulated"`

### Drawing reference string format
`"JS-PE-DPS-XXXX"` or `"JS-PE-DPS-XXXX-00N"` (multi-sheet).  
`_drawing_base()` strips the `-00N` suffix to get the 4-digit key for `DRAWING_SIZE_RANGES`.  
FRP saddle sub-ranges use a 2-digit suffix (e.g. `0701-01`) — not stripped by `_drawing_base()`.

### `/api/select` — request body
```json
{
  "nps": 4.0,
  "material": "CS",
  "pwht": false,
  "insulation": "uninsulated",
  "function": "rest",
  "piping_class": "BB3",
  "refinements": {},
  "is_flange": true,
  "flange_class": 150,
  "pipe_orientation": "horizontal",
  "vertical_restraint": null
}
```
`is_flange` defaults to `false`. `flange_class` is an integer or `null`.  
For FRP material, `flange_class` is ignored (FF71 is always returned).  
Flange params are ignored when `function != "rest"`.
For vertical supports, send `pipe_orientation="vertical"` and `vertical_restraint="sliding"` or `"fixed"`. The backend uses insulation (`uninsulated` / `hot_insulated`) to distinguish bare vs insulated WL supports.

### `/api/select` — response
```json
{
  "success": true,
  "status": "complete",
  "support_code": "FLANGE FRAME (FF01)",
  "drawings": ["JS-PE-DPS-0417"],
  "drawings_labeled": [{"code": "FF01", "ref": "JS-PE-DPS-0417"}],
  "related_drawings": [],
  "related_drawings_labeled": [],
  "notes": [],
  "refinement_questions": [],
  "applied_refinements": [],
  "refinement_warnings": [],
  "is_applicable": true,
  "image_key": "bearing_plate",
  "size_range": "2_to_16",
  "piping_class": "BB3"
}
```
`status` is `"complete"` | `"needs_refinement"`.  
`image_key` for FF01–FF06 returns `"flange_frame"`; for FF71 returns `"frp_flange_holder"`.
Dedicated SVGs exist at `static/images/supports/flange_frame.svg` and `frp_flange_holder.svg`.
The metallic SVG is finalized as a side-elevation flanged-valve support with pipe, bolted flanges, valve body, support frame, base plate, and exact selected-code label substitution (`FF01`, `FF02`, etc.). The FRP SVG is finalized as a green FRP flanged valve holder with the support clearly under the valve/flange area and FF71-only labeling.

`image_key` for WL03–WL06 returns `"vertical_lug"`. `static/images/supports/vertical_lug.svg` is a blueprint-style vertical lug schematic.

### `/api/drawing/<ref>?nps=<nps>` response
Returns `application/pdf` bytes inline. 404 if ref not in `DRAWING_PAGES` or PDF missing.

---

## Material Class Aliases (selector.py)

| User input | Normalised key | PWHT sub-keys? |
|---|---|---|
| CS, LT, cladded | `cs_lt` | Yes — `pwht` / `no_pwht` |
| SS, DS, SD, SA | `ss_ds_sd_sa` | No |
| AL, AY, CN | `al_ay_cn` | No |
| FRP, GRP, fiberglass | `frp` | No (special-case path) |

---

## Frontend State (app.js)

```javascript
let state = {
  nps:              null,          // float or null
  material:         "",            // raw dropdown value e.g. "CS"
  pwht:             false,
  insulation:       "uninsulated", // "uninsulated" | "hot_insulated"
  fn:               null,          // "rest" | "guide" | "line_stop" | "hold_down"
  pipingClass:      "",            // MPMS class code e.g. "BB3"
  pipingClassEntry: null,          // resolved entry from /api/resolve-class
  refinements:      {},
  pendingQuestions: [],
  pipeOrientation:  "horizontal", // "horizontal" | "vertical"
  verticalRestraint: null,        // "sliding" | "fixed"
  // Flange support (REST only — ignored by backend for other functions)
  isFlange:    false,
  flangeClass: null,  // int: 150 | 300 | 600 | 900 | 1500 | 2500 (ignored for FRP)
};
```

`bindFlangeControls()` wires up the flange toggle and pressure-class buttons.  
`_updateFlangeClassVisibility()` hides the pressure-class section when FRP is selected.  
`_resetFlangeState()` is called when the function changes away from REST.  
Flange section (`#flangeSection`) is hidden by default; shown only when REST is selected.

---

## Environment

| Platform | Entry point | Notes |
|---|---|---|
| Railway (prod) | `python app.py` via Procfile | PDF must be at repo root |
| Local (Windows) | double-click `run_local.bat` | activates .venv if present |
| Local (manual) | `python app.py` | `http://localhost:5000` |

**PDF location:** repo root = `/app/QW2507-00-PE-STD-00001.pdf` on Railway.  
Override with env var `PDF_PATH` if stored elsewhere.  
**Python:** 3.7+ required. Tested on 3.13.  
**No database** — all data is in Python dicts in source files.

---

## Test Suite

**Files:** `tests/test_selector.py`, `tests/test_span.py`, `tests/test_rack.py`, `tests/test_rack_geometry.py`, `tests/test_rack_dxf.py`  
**Framework:** pytest  
**Count:** 502 tests, 0 failures (UI redesign added no tests — markup/CSS only)

| Class | Tests | Covers |
|---|---|---|
| `TestGetSizeRange` | 15 | REST and TABLE 16 size-range boundaries |
| `TestNormalizeMaterial/Insulation/Function` | 22 | All normalizer aliases and error cases |
| `TestRestComplete` | 12 | Deterministic REST paths (no refinement) |
| `TestRestNeedsRefinement` | 6 | Triggers for orientation/wall/temp questions |
| `TestRestRefinementResolution` | 12 | Full refinement chains |
| `TestGuideSelection` | 9 | All GUIDE paths including FRP |
| `TestLineStopSelection` | 12 | All LINE STOP paths including FRP deviation |
| `TestHoldDownSelection` | 7 | All HOLD DOWN paths |
| `TestFrpSpecialCases` | 11 | FRP-specific routing for all four functions |
| `TestDrawingReferences` | 7 | Drawing lookup, labeling, FF01/FF06/FF71 refs |
| `TestObsoleteCodesRemoved` | 6 | SC09 and CF04 confirmed absent |
| `TestEdgeCases` | 9 | NPS bounds, unknown inputs, boundary values |
| `TestFlangeFrameSupports` | 29 | FF01–FF06: codes, drawings, NPS bounds, metallic materials, error cases |
| `TestFF71FrpFlangeHolder` | 7 | FF71: NPS bounds, drawing, FRP routing (no class required) |
| `TestFlangeImageKeys` | 5 | FF01–FF06 → flange_frame; FF71 → frp_flange_holder; neither → bearing_plate |
| `TestFFDrawingPages` | 10 | All FF refs in DRAWING_PAGES; page numbers verified (FF01=111, FF06=116, FF71=179) |
| `TestFFPdfHighlighting` | 8 | FF71 special-case row detection for NPS 10/18; FF01–FF06 generic row detection still works |
| `TestVerticalPipeLugSupports` | 22 | WL03–WL06 logic, FRP blocking, NPS range, warning, drawings, related refs, API payload |
| `TestWLPdfHighlighting` | 9 | WL column-highlighting mode, column rectangles for NPS 12/24, standard row mode unchanged |
| `tests/test_span.py` | 47 | Support span calculator |
| `tests/test_rack.py` | 53 | Pipe rack calculator (math, formulas) |
| `tests/test_rack_geometry.py` | 149 | Rack geometry model + SVG schematic (two-scale sizing, center-spare placement, dimensioning, arrows) |
| `tests/test_rack_dxf.py` | 13 | Rack DXF export (mm units, layers, circles, spare zone, drafting zones, short shoes, route response) |

---

## UI Platform Shell & Redesign (2026)

The product was reframed from "a Support Selector with extra pages" into a **JESA-endorsed Piping
Engineering Tools Platform**. This is a **markup/CSS/asset-only** effort: **no Python logic, routes,
calculations, or `app.js` were changed**, and the 502-test suite stayed green throughout. The
redesign followed the approved plan in `C:\Users\hp\.claude\plans\ticklish-rolling-treehouse.md`
(internally code-named "DATUM"); see `DESIGN_DECISIONS.md` for the settled decisions.

**App shell (all 5 pages).** Every page renders inside a shared shell via partials:
- `_shell_open.html` — slim top bar: **JESA seal + "Piping Engineering / Tools Platform" lockup**
  → home, breadcrumb from `tool_title`/`tool_subtitle`, a `⌘K` command-palette button, theme toggle.
  Opens `.workspace` + `.workspace-main`.
- `_rail.html` — persistent **global left rail** grouped by capability domain
  (Workspace · Selection · Verification · Arrangement · Reference). Uses the `datum-icons.svg`
  drafting-glyph sprite. Active item driven by the existing `active_page` template var. Collapses to
  an icon-only strip ≤1100px.
- `_shell_close.html` — closes the shell, includes `_footer.html`, and includes
  `_command_palette.html`.
- `_command_palette.html` — self-contained `⌘K` palette (inline JS, **not** `app.js`): jump to a
  tool, toggle theme. Esc closes. Included on all 5 pages.

`_navbar.html` is **retired/unused**. The Support Selector keeps its own step sidebar as a
*secondary* in-tool rail beside the global rail.

**Workspace Home (`/`, `landing.html`).** An operational home, not a marketing page:
- **Hero** — desaturated plant photo (`static/images/brand/hero-plant.png`, wired via `--hero-photo`)
  behind layered navy scrims + a faint blueprint grid; the photo is *atmosphere only*. Minimal,
  confident copy: a JESA-sealed kicker, headline "Piping engineering tools, organized for daily
  design work.", sub-line "Professional tools in one governed platform.", and a one-line lede about
  selecting supports, verifying spans, arranging racks, and accessing references. No document codes in the hero (they live in the Standards register);
  the old rack illustration was removed for a unified atmosphere.
- **Tool choice band** — "Choose a tool" entry card with a neutral `--datum` CTA ("Open a tool ⏎").
- **Tool category rail** — independent chips for Support selection, Span verification, Rack
  arrangement, and References. No arrows or mandatory progression.
- **Available Engineering Tools** — the four tool cards (+ placeholders) as sheet-cards, each with
  status, drafting-glyph icon, purpose, explicit output, and a title-block-style footer carrying an
  engineering reference tag (Tables 15 & 16 · KS-PE-SPC-0073 · DXF export · Span data & codes).
- **Standards & Traceability register** — `sheet--authority` panel with a navy "GOVERNED" seal and
  name↔mono-code rows (QW2507… / Tables 15 & 16 / Index / KS-PE-SPC-0073). Reads as "this platform
  is governed," not "a list of documents."

**Design system (style.css).**
- Semantic token layer in `:root` + `[data-theme="dark"]`. Key tokens: `--datum` (teal, the single
  interactive accent), `--datum-soft`, `--annotation` (amber), `--authority` (JESA navy — seal/
  title-block ONLY, never interactive), `--pass`/`--fail`, elevation `--e1/e2/e3`, `--font-display`
  (Saira Semi Condensed), `--font-mono` (JetBrains Mono), `--font-ui`/`--font-body` (Inter),
  `--anim-fast`/`--anim-med`, `--radius`/`--radius-lg`, `--surface-sheet`, `--ink`,
  `--dimension-line`, `--space-unit: 4px`, hero scrim tokens.
- **No hardcoded hex** in CSS rules outside `:root`/dark (neutral `rgba(255,255,255,…)` /
  `rgba(0,0,0,…)` overlays on dark bands are an accepted pre-existing convention).
- **Drawing-sheet card** primitive (`.sheet` / `.sheet-tb` / `.sheet-body`) and **result sheet**
  (`.result-titleblock` + `.result-traceability` + `.result-next` handoff to `/span`) — result sheet
  is static markup inside the JS-toggled `#resultContent`, so all `app.js` ids are unchanged.
- **Icon sprite** `static/images/icons/datum-icons.svg` — 20×20 grid, 1.75 stroke, no fills,
  `currentColor`; one coherent drafting-glyph family, referenced via external `<use>`.

**Phase 2.5 — Professional Polish Pass (complete, markup/CSS only).** A "0.9 → 1.0" finish pass on
the Workspace Home: trimmed hero copy; neutral "Choose a tool" entry card; independent tool category
chips; tool-card footer reference tags + relocated index (fixed an index/status overlap defect) + a
single coherent `--datum` interaction language + `:focus-visible` rings; Standards governance
register with the authority seal; more readable (still discreet) footer credit; spacing/density
tightening; icon left-alignment at 40px. 502 tests green; all 5 routes 200.

**Remaining redesign work:** Phase 3 remains gated and paused. Do not implement the shared **Line
object**, cross-tool handoff, or unified connected workflow until explicitly approved. Full
strategy in the approved plan.

---

## Current Project Status

Phase 2.1 Flange Supports are complete and fully end-to-end functional:
- FF01–FF06 metallic flange-frame support logic is complete, selected by pressure class and NPS range.
- FF71 FRP flanged valve/component support logic is complete, selected by NPS with no pressure class required.
- Drawing references and NPS filtering are complete for 0417–0422 and 0705.
- PDF drawing opening/highlighting is fixed and verified, including FF71 NPS 10 and 18.
- SVGs are refined and finalized for metallic FF01–FF06 and FF71 FRP.
- Current test status: 335 passed.

Phase 2.2A Vertical Pipe Lug Supports are complete:
- WL03–WL06 implemented for true vertical pipe lug support selections.
- WL01/WL02 intentionally deferred as special welded lug attachment details.
- FRP is blocked for WL supports with a not-applicable message.
- Stress-engineer approval/local stress-check warning is shown for every WL03–WL06 result.
- PDF column highlighting is fixed for WL drawings.
- Related/referenced drawing links are added as secondary clickable drawing chips.

Phase 2.3 Rack Calculator Schematic Refinement is complete:
- `rack_geometry.py` builds a true-scale (mm) `RackGeometry` model from `calculate_rack()` output;
  `rack_diagram.py` renders it to SVG with a two-scale model (true-scale positions, uniform
  symbol-scale envelope sizing).
- "Center" future spare space is inserted **between pipes** near the middle of the pipe list by
  index (`gap_index = (n-1)//2`), positioned between the flanking pipes' outer envelopes with
  balanced clearance on each side; tight gaps get a symmetric (equal) overlap plus a
  `geo.warnings` note rendered in the SVG.
- Bottom dimensions simplified to `Occupied Width = XXXX mm` (annotation) + rack width CL-CL +
  `Future spare space = XX mm` — no L+R=total summation.
- Uniform pipe label format and label-block height; dimension arrows fixed to point outward via
  paired Start/End SVG markers.
- `rack_dxf.py` exports the same approved `RackGeometry` to DXF using `ezdxf`; DXF is layout/export
  only and does not derive from SVG or alter any rack sizing formulas.
- DXF output uses real millimetre modelspace (`$INSUNITS = 4`) and preserves approved pipe CLs,
  column CLs, rack width, spare width, pipe OD, insulation OD, and flange OD.
- DXF V2.1 is a designer-ready arrangement drawing with sheet border, title area, rack section,
  top/bottom dimensions, strong rack beam, simplified columns, short shoe/support details,
  centered/hatched future spare zone, P-tags near pipes, pipe schedule, notes, drawing information,
  legend, and envelope callouts.
- Flange OD circles are dashed/light clearance envelopes only; notes clarify that flange-envelope
  overlap in section view does not imply simultaneous flange locations or require rack widening.
- Flask route `/rack-calculator/dxf` downloads the generated DXF and passes profile metadata
  (`HEA 300`, custom width, etc.) into title/info blocks.
- Current test status: 497 passed.

---

## Next Recommended Tasks

1. **Auto-populate flange class from MPMS rating** — `MPMS_SPAN_MAP[code]["rating"]` contains
   `"150 Lb."`, `"300 Lb."` etc.; map to integer and pre-select the pressure class button
2. **Phase 2.2B — Special Welded Lug Attachment Details** (WL01/WL02, deferred from vertical-support selection)
3. **Phase 2.3.5 — Vessel/Equipment Clips** (VC series, pages 74–190 of standard)
4. **Phase 2.4 — Spring Hangers / Remaining Vertical Supports** (GS, SF, UB series)
5. **Deploy and verify** — confirm flange/WL SVGs, drawing links, PDF highlighting, and the
   refined rack-calculator schematic in production
6. **Later expansion** — continue remaining standard support families from pages 74–190 as needed
7. **Regression coverage** — add broader visual/PDF regression checks if drawing behavior grows further
