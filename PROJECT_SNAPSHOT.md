# PROJECT SNAPSHOT — JESA Piping Engineering Tools Platform

**For quick onboarding. Read this first; details live in `CODEX_HANDOFF.md`, `DESIGN_DECISIONS.md`,
`CLAUDE.md`, `CONTEXT.md`.**
**Date:** 2026-06-11 · **Tests:** 502 passing · **Deploy:** Railway (live)

---

## What is the project?

A **Flask web app** for JESA piping/stress engineers — a **JESA-endorsed Piping Engineering Tools
Platform**. It began as a single Pipe Support Selector and grew into a workspace of four engineering
modules behind one shared shell (top bar + left capability rail + `⌘K` palette). It presents as a
drafting-grade engineering instrument: results are stamped, traceable "sheets" backed by governing
standards.

**Modules:** Support Selector (`/support-selector`), Span Calculator (`/span`), Rack Calculator +
DXF export (`/rack-calculator`, `/rack-calculator/dxf`), Reference Tables (`/reference`), and the
Workspace Home launcher (`/`).

**Stack:** Python/Flask, vanilla JS (`app.js`), PyMuPDF (PDF), ezdxf (DXF). No database — all data is
in Python dicts. All source at repo root (Railway requirement). Entry: `app.py`.

---

## What is completed?

- **Engineering engine (mature, fully tested):** Support Selector (Tables 15 & 16; all materials;
  PWHT/insulation; refinements; FRP path), flange supports FF01–FF06 + FF71, vertical lugs WL03–WL06,
  Span Calculator, Rack Calculator, drawing/PDF highlighting system.
- **Rack DXF pipeline:** `calculate_rack()` → `rack_geometry.py` (true-scale mm model) →
  `rack_diagram.py` (SVG) / `rack_dxf.py` (designer-ready DXF).
- **Platform redesign (markup/CSS/assets only):** shared shell + capability rail + `⌘K` palette;
  rebuilt Workspace Home; removed invented "DATUM" UI branding; retained JESA endorsement; refined
  hero (subtle plant-photo atmosphere); **Phase 2.5 professional polish pass** (numbered workflow
  spine, tool-card footers, single `--datum` accent, focus rings, Standards governance register).
- **502 tests green; all 5 routes return 200; both light/dark themes work.**

## What is in progress?

- **Nothing is actively being implemented.** The just-completed work is documentation/handoff.
- Optional, not started: propagating the Workspace Home polish to the four tool pages + shell.

## What is next?

1. **Phase 3 (GATED — needs explicit user approval):** shared **Line object** (NPS/material/class)
   via additive inline scripts + `sessionStorage['datum-line']` (**no `app.js`**); cross-tool
   handoff Selector → Span → Rack; the Continue band lights up; unified Result Sheet.
2. **Tool-page polish propagation** (low-risk follow-up).
3. **Engine expansion** (pages 74–190): WL01/WL02 details, vessel/equipment clips (VC), spring
   hangers (GS/SF/UB). Quick win: auto-populate flange class from MPMS `rating`.

---

## What should NEVER be changed (without explicit approval)?

1. **Engineering calculations & business logic** — `selector.py`, `support_rules.py`,
   `rack_calculator.py` (formulas locked), `rack_geometry.py`, `rack_dxf.py`, `pdf_service.py`, etc.
2. **`app.js`** — never for UI work. Use inline `<script>` / `_command_palette.html`; add result
   markup *statically* inside `#resultContent`.
3. **Flask routes & repo-root file layout** — Railway + `from selector import …` depend on them.
4. **Approved architecture & direction** — workspace shell, capability rail, "one governed workflow"
   framing, Workspace Home structure. Do not redesign.
5. **Token layer** — no hardcoded hex outside `:root`/`[data-theme="dark"]` (neutral white/black
   rgba overlays on dark bands excepted). Keep both themes correct.
6. **All 502 tests must stay green.**
7. **Internal DATUM code names** (`--datum`, `.datum-grid`, `datum-icons.svg`, `datum-line`) are
   frozen — do not rename; never reintroduce visible "DATUM" text.

---

## Run / verify

- Local: double-click `run_local.bat` (or `python app.py` → `http://localhost:5000`).
- Tests: `python -m pytest -q` (expect **502 passed**).
- Always verify visual changes in **both** themes and re-run the suite.
