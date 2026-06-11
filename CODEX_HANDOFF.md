# CODEX HANDOFF — JESA Piping Engineering Tools Platform

**Date:** 2026-06-11 · **Status:** Stable, deployed (Railway), 502 tests passing
**Read order for onboarding:** this file → `PROJECT_SNAPSHOT.md` → `DESIGN_DECISIONS.md` →
`CLAUDE.md` → `CONTEXT.md`. The approved design plan is
`C:\Users\hp\.claude\plans\ticklish-rolling-treehouse.md`.

> This document hands the project from Claude to Codex (or any new coding agent). Its job is to let
> you continue **without re-running settled design discussions** and **without breaking approved
> architecture or engineering logic**.

---

## Executive Summary

A Flask web app for JESA piping/stress engineers. It started as a single **Pipe Support Selector**
and has grown into a **JESA-endorsed Piping Engineering Tools Platform** with four engineering
modules behind a shared application shell. The engineering engine is mature and fully tested (502
pytest tests, all green) and is deployed live on Railway.

Recent work has been a **presentation-layer redesign** (markup/CSS/assets only — no engine, no
routes, no `app.js`): a workspace shell + command palette, a rebuilt Workspace Home, a removed
invented "DATUM" product name, retained JESA endorsement branding, a refined hero, and a
"version 0.9 → 1.0" professional polish pass. The engine and tests were never touched.

**What's next:** Phase 3 (gated) — a shared **Line object** that threads NPS/material/class across
tools — plus propagating the polish to the four tool pages, then scaling engineering coverage.

---

## Completed Work

### Engineering engine (mature, fully tested — do not change without approval)
- **Support Selector** (`selector.py`, `support_rules.py`): REST / GUIDE / LINE STOP / HOLD DOWN per
  Tables 15 & 16; all material classes (CS/LT, SS/DS/SD/SA, AL/AY/CN, FRP); PWHT + insulation
  branching; conditional refinement questions; FRP special-case path.
- **Flange supports (Phase 2.1):** FF01–FF06 (metallic, by ASME class) + FF71 (FRP), end-to-end with
  drawings, PDF highlighting, and finalized SVGs.
- **Vertical pipe lug supports (Phase 2.2A):** WL03–WL06, end-to-end with dedicated PDF column
  highlighting and related-drawing chips. (WL01/WL02 deferred.)
- **Span Calculator** (`span_calculator.py`): max allowable span per KS-PE-SPC-0073.
- **Rack Calculator** (`rack_calculator.py` — formulas locked): pipe rack width/spacing math.
- **Drawing system** (`drawing_index.py`, `pdf_service.py`): code→drawing mapping, NPS filtering,
  PyMuPDF extraction with row/column highlighting.

### Architecture / platform shell
- Shared shell on all 5 pages: top bar (`_shell_open.html`) + global capability rail (`_rail.html`)
  + footer/palette (`_shell_close.html` → `_footer.html` + `_command_palette.html`).
- Capability-domain rail: Workspace · Selection · Verification · Arrangement · Reference.
- `⌘K` command palette — self-contained inline JS in `_command_palette.html` (**not** `app.js`).
- `_navbar.html` retired.

### Design system
- Semantic token layer in `:root` + `[data-theme="dark"]`: `--datum` (single interactive teal
  accent), `--datum-soft`, `--annotation` (amber), `--authority` (JESA navy — seal only), pass/fail,
  elevation `--e1/e2/e3`, fonts (`--font-display` Saira Semi Condensed / `--font-mono` JetBrains
  Mono / Inter body), motion, radius, hero scrims. No hardcoded hex outside the token layer.
- Drafting-glyph icon sprite `static/images/icons/datum-icons.svg` (20×20, stroke 1.75, no fills).
- Reusable primitives: `.sheet` drawing-sheet card, `.result-titleblock` + `.result-traceability`
  result sheet, `.tool-card` board card, workflow `.wh-spine`.
- Dual theme (light "vellum" / dark "film"), both first-class.

### Workspace Home (`landing.html`)
- **Hero:** desaturated plant photo (`static/images/brand/hero-plant.png` via `--hero-photo`) behind
  navy scrims + faint blueprint grid; minimal confident copy; no document codes in the hero.
- **Continue band:** "Start your workflow" entry card; hydrates from `sessionStorage['datum-line']`.
- **Workflow spine:** numbered, connected chips (01 Select → 02 Verify → 03 Arrange · 04 Reference).
- **The Board:** four tool cards (+ placeholders) with index, status, drafting icon, and a
  title-block footer carrying an engineering reference tag.
- **Standards & Traceability register:** `sheet--authority` panel with a "GOVERNED" seal and
  name↔mono-code rows.

### Phase 2.5 — Professional Polish Pass (complete)
A "0.9 → 1.0" finish pass on the Workspace Home (markup/CSS only): trimmed hero copy; inviting entry
CTA; numbered workflow spine; tool-card footer tags + relocated index (fixed an index/status overlap
defect) + a single coherent `--datum` interaction language + `:focus-visible` rings; Standards
governance register; more readable (still discreet) footer credit; spacing/density tightening; icon
review. **502 tests pass; all 5 routes 200.**

### DXF work (Phase 2.3 / 2.3D)
- `rack_geometry.py`: `calculate_rack()` output → true-scale (mm) `RackGeometry` model.
- `rack_diagram.py`: geometry model → SVG (two-scale sizing, centered spare bay, dimensions).
- `rack_dxf.py`: same geometry → designer-ready DXF (mm modelspace, `$INSUNITS=4`, CAD layers, title
  block, pipe schedule, notes, dashed flange clearance envelopes). Route `/rack-calculator/dxf`.
- The DXF derives only from the approved geometry/calculation pipeline — it never alters sizing math.

---

## Current UI Status

> Screenshots cannot be generated from this CLI environment. To capture before/after images, run
> `run_local.bat`, open each route, and screenshot in **both** light and dark themes.

**Design language:** a drafting / title-block engineering aesthetic. Result outputs read as stamped
"sheets"; numbers/codes are mono (JetBrains Mono, tabular); prominent headings use Saira Semi
Condensed; body is Inter. One interactive accent (teal `--datum`), amber for warnings, JESA navy
reserved for the authority seal. A faint blueprint grid is the recurring base layer. Both themes are
fully supported.

**Pages (all behind the shared shell):**
- `/` Workspace Home — hero atmosphere → Continue band → numbered workflow spine → The Board (4 tool
  cards) → Standards & Traceability register.
- `/support-selector` — input column + result sheet (title block + determination + schematic +
  traceability footer with drawing chips and a `→ Verify span` handoff).
- `/span` — span check.
- `/rack-calculator` — rack math + true-scale schematic + DXF export.
- `/reference` — governing reference tables.

**Polished surface today:** the Workspace Home is fully polished (Phase 2.5). The four tool pages
share the shell and tokens but have **not yet received the same polish/focus-state pass** — that is
the first follow-up after Phase 3 readiness.

---

## Remaining Work

### Phase 2.5 final refinements (small, optional)
- Propagate the Workspace Home polish (card language, `:focus-visible` rings, spacing rhythm) to the
  four tool pages and the shell (rail + top bar) for a uniform keyboard/visual story.
- Verify WCAG AA contrast of `--datum` text on `--datum-soft` in both themes.
- Optional: reduce the Board hover wash to border + corner marks + lift if a more restrained hover is
  preferred (open question raised with the user).

### Phase 3 — Workflow spine / Line object (GATED — needs explicit user go-ahead)
- Shared **Line object** (NPS / material / class) persisted via additive inline scripts +
  `sessionStorage['datum-line']` — **no `app.js` edits**.
- Cross-tool handoff: Selector → Span → Rack carry-forward; the Continue band lights up from the
  stored line; query-param/observer prefill on the next tool.
- Unified Result Sheet treatment across all four tools.

### Future tools (engine expansion, pages 74–190 of the standard)
- WL01/WL02 special welded lug attachment details (Phase 2.2B).
- Vessel / equipment clips (VC series) — needs a new "attached to vessel/equipment?" input axis.
- Spring hangers / remaining vertical supports (GS, SF, UB series) — needs orientation input.

### Future enhancements
- In-context drawing viewer overlay (NPS row highlighted) instead of raw PDF open.
- Auto-populate flange class from MPMS `rating` (Priority 1 quick win — see `CLAUDE.md`).
- Broader visual/PDF regression coverage as the drawing system grows.

---

## Risks / Lessons Learned

- **A prior redesign was rejected** for feeling like a *decorated utility / generic SaaS dashboard*
  rather than a professional piping-engineering instrument. The corrective is the current direction:
  drafting authority + standards traceability, not marketing polish. **Do not drift back toward
  marketing/SaaS aesthetics.**
- **"DATUM" was an invented product name with no user meaning** and was removed from the UI. Do not
  reintroduce visible "DATUM" text. But the internal code names (`--datum`, `.datum-grid`,
  `datum-icons.svg`, `datum-line`) are frozen architecture — **do not rename them**.
- **`app.js`, the Python engine, routes, and calculations are off-limits** for UI work. Several
  constraints exist specifically because earlier changes risked the tested engine. Visual changes go
  in templates/CSS/assets only; the Support Selector result is populated by `id`, so add *static*
  markup inside `#resultContent` rather than editing the render JS.
- **Hardcoded hex creeps in.** A defect-class to watch: colors must come from the token layer.
  The one accepted exception is neutral `rgba(255,255,255,…)`/`rgba(0,0,0,…)` overlays on dark bands.
- **Competing accent hues** made tool cards feel unengineered; consolidating to one `--datum`
  interactive accent was a deliberate fix — keep it.
- **Both themes must be verified** for every visual change; SVG/DXF must read correctly in both.
- **JESA logo is trademarked** — currently a text-stamp lockup; confirm usage before external deploy.
- **All source must stay at repo root** (Railway + `from selector import …`).

---

## Recommended Next Step

**Do not start Phase 3 or any UI change without explicit user approval** — Phase 3 is gated.

When the user gives the go-ahead, the highest-value first task is the **Phase 3 Line object
foundation**: an additive, observer-based inline script that writes/reads
`sessionStorage['datum-line']` (NPS/material/class) **without touching `app.js`**, so the existing
Continue band on the Workspace Home lights up and Selector → Span → Rack can carry a line forward.
Prototype the persistence mechanism first (it is the one real architectural unknown), verify all 502
tests stay green and all 5 routes return 200 in both themes, then build the cross-tool handoff.

If the user instead wants a smaller next step, the **tool-page polish propagation** (apply the
Workspace Home card/focus/spacing language to `/support-selector`, `/span`, `/rack-calculator`,
`/reference`) is low-risk and self-contained.
