# Support Selector — Project Context

## What this app does
Flask web app that helps stress engineers select appropriate support types for piping systems.
Given five core inputs (NPS, material, PWHT, insulation, function) it returns the correct support
type, drawing references, and engineering notes per JESA Piping Support Standard Rev A
(QW2507-00-PE-STD-00001).

## Key files
- `app.py` — Flask entry point and routes
- `selector.py` — Core logic: `select_support()` + `_select_flange_support()`
- `support_rules.py` — Rules engine for standard supports (Tables 15 & 16)
- `drawing_index.py` — Maps support codes → drawing refs; `DRAWING_SIZE_RANGES` for NPS filtering
- `note_refinement.py` — Conditional engineering-note question flow
- `material_classes.py` — MPMS piping class → span material mapping (single source of truth)
- `pdf_service.py` — Drawing extraction + NPS row highlighting (PyMuPDF)
- `span_calculator.py` — Support span calculator
- `rack_calculator.py` — Pipe rack width/spacing math (formulas only — do not change without explicit approval)
- `rack_geometry.py` — Converts `calculate_rack()` output into a true-scale (mm) geometry model (`build_geometry_model()`)
- `rack_diagram.py` — Renders the rack geometry model to SVG (px scaling, two-scale symbol sizing)
- `rack_dxf.py` — Renders the rack geometry model to a designer-ready DXF arrangement drawing (mm modelspace, CAD layers)
- `pipe_flange_data.py` — DN sizes and ASME flange rating data
- `structural_profiles.py` — Eurocode steel column profile widths (HEA/HEB/HEM/IPE)
- `templates/` — HTML templates. Pages: `landing.html` (Workspace Home, `/`), `index.html`
  (support selector), `span_calculator.html`, `rack_calculator.html`, `reference.html`.
  Shared shell partials: `_shell_open.html` (top bar + opens workspace), `_rail.html` (global
  capability rail), `_shell_close.html` (closes shell + footer), `_footer.html`,
  `_theme_toggle_script.html`. `_navbar.html` is retired/unused.
- `static/` — CSS/JS assets (`static/css/style.css` holds all tokens + shell + components)
- `tests/` — Full pytest suite (502 tests, all passing)
- `run_local.bat` — Windows double-click launcher
- `LOCAL_RUN.md` — Local setup and troubleshooting guide

## Deployment
- Platform: Railway
- Repo: github.com/nizari08-max/support-selector
- Entry point: `app.py`
- Procfile: `web: python app.py`
- All source files must stay at repo root (not in subdirectories)

## Architecture note
`app.py` calls `from selector import select_support` — selector.py must stay at root.

## UI design system
The product is a **Piping Engineering Workspace** — a platform shell that contains multiple
engineering modules (see "UI Platform Shell" below). Light + dark themes via `data-theme`.

- **Theme:** Engineering / drafting aesthetic. Light bg `#F0F4F8` / cards `#FFFFFF`; dark bg
  `#0F172A` / panels `#1E293B`. JESA blue header `#003DA5` (light) / `#002B7A` (dark).
- **Accent colors:** Blue `#0057D9` light / `#3B82F6` dark (primary), Amber `#F59E0B`
  (secondary/active/annotation), Green `#059669`/`#10B981` (success). Drafting tokens:
  `--surface-sheet`, `--ink`, `--dimension-line`.
- **Fonts:** `--font-display` = **Saira Semi Condensed** (prominent headings only),
  JetBrains Mono (codes/numbers/data), Inter (body & UI labels) — Google Fonts CDN.
- **Layout:** global **left capability rail** (220px; icon-only ≤1100px) + **slim top bar**
  (52px: wordmark, breadcrumb, theme) + page content. The Support Selector additionally has its
  own 210px in-tool **step sidebar** (hidden ≤1100px); single column ≤960px.
- **All colors** defined as CSS variables in `:root` (+ `[data-theme="dark"]`) — no hardcoded hex
  in CSS rules.
- **Reusable components:** app shell (`.topbar`/`.rail`/`.workspace`), drawing-sheet card
  (`.sheet`/`.sheet-tb`/`.sheet-body`), result sheet (`.result-titleblock`/`.result-traceability`).
- **Do not touch `app.js`** when making visual changes — use inline `<script>` in the HTML
  template instead. (The Support Selector result is JS-populated by `id`; add *static* markup
  inside `#resultContent` and style it rather than changing the render JS.)

---

## Approved Architecture (do not redesign)

The platform's structure is **settled**. New agents should build *within* it, not reorganize it.
Full rationale is in `DESIGN_DECISIONS.md`; quick onboarding is in `PROJECT_SNAPSHOT.md` and
`CODEX_HANDOFF.md`.

- **Workspace concept.** The product is a **JESA Piping Engineering Tools Platform** — a single
  workspace containing multiple engineering modules behind a shared app shell. It is *not* "a
  Support Selector with extra pages."
- **Navigation structure.** Shared shell on all 5 pages: slim **top bar** (JESA lockup + breadcrumb
  + `⌘K` + theme) via `_shell_open.html`; global **left capability rail** via `_rail.html`;
  `_shell_close.html` (footer + `_command_palette.html`). The Support Selector additionally has its
  own in-tool step sidebar. This navigation model is approved — do not replace it.
- **Capability domains.** The rail is grouped by domain: **Workspace · Selection · Verification ·
  Arrangement · Reference**. New modules slot into one of these domains rather than spawning a new
  top-level nav paradigm.
- **Module relationships / tool-hub philosophy.** The four live tools are independent modules under
  one governed platform: Support selection, Span verification, Rack arrangement, and Engineering
  references. Communicate shared standards and visual consistency without implying automatic
  cross-tool data carryover.
- **Workspace Home (`/`).** An operational launcher (hero atmosphere → tool choice band →
  available engineering tools → Standards register), not a marketing landing page.
- **`⌘K` command palette.** Lives in `_command_palette.html` with self-contained inline JS — **never
  in `app.js`**. New commands are added here.
- **Future cross-tool state (Phase 3, gated and paused).** Do not implement or imply the shared
  **Line object** / cross-tool workflow until explicitly approved. Existing live tools remain
  technically independent.

## Approved Design Decisions (settled — do not relitigate)

- **DATUM branding REMOVED from the UI.** The invented "DATUM" product name was dropped — it has no
  meaning to end users. Do **not** reintroduce visible "DATUM" text anywhere. DATUM survives ONLY as
  internal, non-user-visible code names (CSS token `--datum`, class `.datum-grid`, sprite
  `datum-icons.svg`, `sessionStorage['datum-line']`) — **do not rename these** (architecture frozen).
- **Official JESA branding retained as endorsement.** JESA = authority/endorsement, not decoration.
  Use the reserved `--authority` token (JESA navy) for the seal/title-block strip **ONLY** — never
  as an interactive color, hero watermark, or splash. Currently a text-stamp lockup (official logo
  asset pending; confirm trademark usage before any external production deploy).
- **Hero philosophy.** Minimal, confident, authoritative copy ("as little text as possible"); a
  desaturated plant photo as *subtle atmosphere only* behind navy scrims + a faint blueprint grid;
  the message stays primary; **no document codes in the hero** (they live in the Standards register);
  no marketing/SaaS hero treatment.
- **Tool-card philosophy.** Each card is a drafting "sheet": mono index, "Live"/"Soon" status,
  drafting-glyph icon, and a title-block footer carrying a real engineering reference tag. One
  coherent interactive accent (`--datum`) per card — do not reintroduce competing hues.
- **Tool-hub communication strategy.** Present the product as professional piping engineering tools
  in one place. Each tool stands alone while sharing the same standards basis, visual language, and
  reference environment.
- **Visual language.** Engineering/drafting aesthetic: result "sheets," title blocks, blueprint
  grid, Saira Semi Condensed display + JetBrains Mono data + Inter body. Dual theme mandatory.
  Reference points: Bentley/AVEVA/Hexagon (authority), Linear (velocity), Stripe/Notion (typography).

## Things That Should NOT Be Changed (explicit constraints)

These are **hard constraints**. Violating them is a regression even if the result "looks fine":

1. **Engineering calculations & business logic.** Do **not** alter `selector.py`, `support_rules.py`,
   `note_refinement.py`, `material_classes.py`, `drawing_index.py`, `span_calculator.py`,
   `rack_calculator.py`, `rack_geometry.py`, `rack_dxf.py`, or `pdf_service.py` logic without
   explicit user approval. `rack_calculator.py` formulas are especially locked.
2. **`app.js`.** Never edit it for visual/UI work. Use inline `<script>` in templates or
   `_command_palette.html`. Result markup is added *statically* inside `#resultContent`.
3. **Flask routes & architecture.** Do not add/rename/remove routes or move source files out of the
   repo root (Railway requires root-level source; `app.py` imports `from selector import …`).
4. **Approved navigation model & platform direction.** Do not redesign the shell, rail, capability
   domains, or Workspace Home structure. Do not reintroduce active connected-workflow or Line-object
   language until Phase 3 is explicitly approved.
5. **The token layer.** No hardcoded hex in CSS rules outside `:root`/`[data-theme="dark"]` (neutral
   `rgba(255,255,255,…)`/`rgba(0,0,0,…)` overlays on dark bands are the one accepted exception).
   Both light and dark themes must stay correct.
6. **The test suite.** All 502 pytest tests must stay green. UI work touches no tested code paths.
7. **Internal DATUM code names** (`--datum`, `.datum-grid`, `datum-icons.svg`, `datum-line`) — frozen,
   do not rename; and do not reintroduce visible "DATUM" text.

---

## Current Project Status

**Last updated:** 2026-06-11  
**Test suite:** 502 tests — all passing  
**Deployment:** Railway (live)  
**Handoff docs:** `CODEX_HANDOFF.md` · `DESIGN_DECISIONS.md` · `PROJECT_SNAPSHOT.md`

### Completed features

**UI Platform Redesign — Workspace shell (markup/CSS only; no logic/`app.js`/route changes)**
- Reframed from "a Support Selector with extra pages" into a **Piping Engineering Workspace**.
- **App shell** across all 5 pages via `_shell_open.html` (slim top bar) + `_rail.html` (global
  capability rail: Selection / Verification / Arrangement / Reference, active via `active_page`,
  collapses ≤1100px) + `_shell_close.html` (footer). Pages migrated by swapping the old
  `_navbar.html`/`_footer.html` includes; `_navbar.html` is now retired.
- **Workspace Home** (`landing.html`, `/`): context header band → Modules launcher → Capabilities
  strip → Standards & Roadmap panels (on the `.sheet` primitive).
- **Design system:** added tokens `--font-display` (Saira Semi Condensed), `--surface-sheet`,
  `--ink`, `--dimension-line`, `--space-unit`. Display font applied to prominent headings only
  (data stays mono, body stays Inter). New **drawing-sheet card** (`.sheet`) and **result sheet**
  (`.result-titleblock` + `.result-traceability` + `.result-next` handoff to `/span`) — result
  sheet is static markup inside the JS-toggled `#resultContent`, so all `app.js` ids are unchanged.
- Remaining (optional): NPS prefill on the cross-tool handoff (inline observer, not `app.js`),
  promote rack SVG/DXF as the Arrangement centerpiece, optional project/session layer.

**Core selector engine**
- REST / GUIDE / LINE STOP / HOLD DOWN — full Tables 15 & 16 rules
- All material classes: CS/LT, SS/DS/SD/SA, AL/AY/CN, FRP
- PWHT and insulation branching; conditional refinement questions (orientation, wall schedule, temperature, axial-stop)
- FRP special-case path: SC71/SC72 (rest), SC73 (guide), CF03 deviation (line stop), N/A (hold down)
- SC09 and CF04 fully removed from all rule strings, mappings, and comments
- `material_classes.py` is the single source of truth for MPMS; `MPMS_CLASSES`/`MPMS_EXCLUDED` removed from `app.js`
- Developer-specific PDF path removed from `pdf_service.py`

**Phase 2.1 — Flange Supports**
- Completed end-to-end: selector logic, UI flow, drawing refs, PDF extraction/highlighting, and finalized SVG illustrations
- FF01–FF06: metallic REST flange-frame supports, selected by ASME pressure class
  - CL150/FF01 (1"–24"), CL300/FF02 (1"–24"), CL600/FF03 (2"–16"),
    CL900/FF04 (2"–16"), CL1500/FF05 (2"–16"), CL2500/FF06 (2"–12")
- FF71: FRP flanged valve/component support, selected by NPS (1"–18"), no pressure class
- `select_support()` gains three keyword params: `is_flange`, `flange_class`, `flange_component`
- `_select_flange_support()`: `valve_flange+FRP → FF71`; `pipe_flange+any → FF01–FF06`; non-REST ignores the flag
- Drawings 0417–0422 and 0705 in `DRAWING_INDEX` + `DRAWING_SIZE_RANGES`
- UI: "Support at a flange?" toggle (REST only) → Component type → Pressure class buttons
- Front-end validation: pressure class required when component = pipe flange
- `static/images/supports/flange_frame.svg` finalized as a side-elevation metallic flanged-valve support with pipe, bolted flanges, valve body, support frame, base plate, and exact selected-code bottom label (`FF01`, `FF02`, etc.)
- `static/images/supports/frp_flange_holder.svg` finalized as a green FRP flanged valve holder with padded support frame under the valve/flange area and FF71-only labeling

**Phase 2.2A — Vertical Pipe Lug Supports**
- Completed end-to-end for true vertical pipe lug supports WL03–WL06 only
- WL03: shear lug / sliding vertical bare pipe
- WL04: fixed lug / vertical bare pipe
- WL05: shear lug / sliding vertical insulated pipe
- WL06: fixed lug / vertical insulated pipe
- WL01/WL02 intentionally deferred as special welded lug attachment details, not vertical-pipe support selections
- Vertical branch uses pipe orientation + insulation + restraint type and bypasses normal horizontal REST/GUIDE/LINE STOP/HOLD DOWN rules
- NPS range: 1"–24"; FRP is blocked for WL supports with a clear not-applicable message
- Warning added for all WL03–WL06 results: use only when specified on stress isometrics or approved by stress engineer; local stress checks may be required
- Drawings 0386–0389 added with WL-specific PDF column highlighting for NPS columns instead of generic horizontal row highlighting
- Related/referenced drawing chips added:
  - WL03 / 0386 → related 0387
  - WL04 / 0387 → related 0386
  - WL05 / 0388 → related 0386
  - WL06 / 0389 → related 0386 and 0388

**Drawing system**
- `get_drawings()` parses support-code string via regex → looks up `DRAWING_INDEX`
- NPS filtering via `DRAWING_SIZE_RANGES` — only sheets covering the selected NPS shown
- Each chip labeled with support code via `label_drawings()`; `drawings_labeled` in API response
- PDF extraction with yellow NPS-row highlighting; x-band approach for rotation=270 pages
- Highlight overflow fix: table y-bounds detected from column-header anchors
- FF71 / `JS-PE-DPS-0705` PDF opening and NPS row highlighting fixed with a dedicated FF71 row-detection path for bare NPS labels such as `10` and `18`
- FF01–FF06 PDF drawing/highlight behavior verified after the FF71 fix
- WL03–WL06 PDF highlighting uses a dedicated column-highlighting path for vertical lug tables; standard supports and FF drawings keep their existing row-highlighting behavior
- Related drawing metadata is returned by the API as secondary clickable drawing references

**Additional features**
- DN → NPS quick converter (inline above NPS grid)
- MPMS piping class input auto-fills material dropdown via `/api/resolve-class/<code>`
- Support Span Calculator (`/span`)
- Pipe Rack Width Calculator (`/rack-calculator`)
- Dark/light theme toggle
- `run_local.bat` Windows launcher (activates .venv, installs deps, opens browser)

**Phase 2.3 — Rack Calculator Schematic Refinement**
- 3-stage pipeline: `calculate_rack()` (math, untouched) → `build_geometry_model()` (true-scale mm geometry) → `render_svg()` (px-scaled SVG)
- Two-scale rendering model: position scale (`scale`, px/mm) places centerlines/dimensions at true scale; a separate uniform `sym_scale_factor` (≤1) scales pipe/flange/insulation envelope radii so the rack's tightest envelope just fits, preserving relative OD ordering (DN900 > DN200, higher flange class → larger OD, insulation increases envelope). `MIN_PIPE_R_PX`/`ENVELOPE_CLEARANCE_PX` remain as last-resort floors applied after `sym_scale_factor`.
- "Center" future spare space = inserted **between pipes** near the middle of the pipe list by index (`gap_index = (n-1)//2`: 4 pipes → between P2/P3, 5/6 pipes → between P3/P4) — not forced onto the rack's geometric centerline.
- The spare bay is positioned between the flanking pipes' outer envelopes (flange/insulation OD) with **balanced (equal) clearance on each side**; if the gap is too tight, clearance is still kept symmetric (equal small overlap) and `geo.warnings` gets a "could not maintain full clearance" note shown as an SVG annotation.
- Bottom dimensions: single `Occupied Width = XXXX mm` annotation (style `"annotation"`, no dimension line/arrows) + `rack width CL-CL` total + `Future spare space = XX mm`. No more "L + R = total" summation format.
- Uniform pipe label format (`P1` / `DN250 #150` / `Ins 20 mm`), uniform 3-row label block height (31px) for all pipes regardless of insulation.
- Dimension arrowheads use separate Start/End marker variants per color (`dimArrow*Start`/`dimArrow*End`) so both ends point outward toward the extension lines.
- Tests: `tests/test_rack_geometry.py` (incl. `TestCenterSpareBetweenEnvelopes`, `TestTwoScaleSymbolSizing`, `TestValidationMatrixH`, etc.)

**Phase 2.3D — Rack DXF Export / Designer-Ready Arrangement Drawing**
- `rack_dxf.py` exports the approved `RackGeometry` model directly to DXF using `ezdxf`; it does **not** derive geometry from SVG and does **not** modify `rack_calculator.py`.
- DXF uses real millimetre modelspace coordinates and sets `$INSUNITS = 4`; pipe CLs, column CLs, rack width, spare width, pipe OD, insulation OD, and flange OD all remain driven by the approved geometry/calculation pipeline.
- CAD layers include rack columns/beams, pipe OD, insulation OD, dashed flange clearance envelopes, future spare zone, dimensions, centerlines, hatch, text, notes, schedule, title block, drawing info, legend, and callouts.
- V2.1 drafting improvements: sheet border; title area; rack section; top/bottom dimensions; clear rack beam; simplified column graphics; short shoe/support details; centered/hatched future spare; P-tags near pipes; detailed pipe data moved to a pipe schedule; separated notes/drawing information/legend zones.
- Flange envelopes are explicitly shown as dashed clearance/maintenance envelopes only, with a note clarifying that overlapping flange envelopes do not indicate simultaneous flange locations or require rack widening.
- Flask route `/rack-calculator/dxf` downloads the generated DXF and passes selected profile metadata into the drawing title/info blocks.
- Tests: `tests/test_rack_dxf.py` covers DXF generation, mm units, required layers, pipe circles, spare zone, dashed flange envelopes, centerline layer, title/schedule/notes/drawing zones, short shoe details, schedule spacing, route response, and immutability of calculation results.

### Nothing currently in progress

---

## Next Recommended Tasks

### Priority 1 — Auto-populate flange class from MPMS (30 min)
When an MPMS class is entered, the `rating` field in `MPMS_SPAN_MAP` already contains the pressure
class string (e.g. `"150 Lb."`). Map these to the integer expected by the flange section
(`150 → 150`, `300 → 300`, etc.) and pre-select the pressure class button automatically.

### Priority 2 — Phase 2.2B: Special Welded Lug Attachment Details
WL01/WL02 attachment details. Treat as special attachments, not as true vertical pipe lug support selections.

### Priority 3 — Phase 2.3.5: Vessel / Equipment Clips
VC series. New input required: "Is this support attached to a vessel or piece of equipment?"
Different selection axis from standard pipe supports.

### Priority 4 — Phase 2.4: Spring Hangers / Remaining Vertical Supports
GS, SF, UB series from pages 74–190 of the standard PDF. Requires orientation input.

### Priority 5 — Deploy and verify
Push to Railway; confirm flange/WL SVGs, drawing links, and PDF highlighting work in production.

### Later roadmap
- Continue expanding remaining standard support families from pages 74–190 as needed
- Add broader visual/PDF regression coverage if the drawing system grows further
