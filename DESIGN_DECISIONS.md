# DESIGN DECISION LOG — JESA Piping Engineering Tools Platform

**Purpose:** record the major decisions made during the redesign so future agents **do not revisit
already-settled questions**. Each entry is a decision, its rationale, and its status. Unless the
user explicitly reopens one, treat every entry here as **final**.

**Last updated:** 2026-06-11

---

### D1 — "DATUM" branding removed from the UI
**Decision:** Drop the invented product name "DATUM" from everything user-visible. The product
presents purely as **JESA · Piping Engineering · Tools Platform**.
**Why:** "DATUM" had no meaning to end users (JESA engineers); an invented brand name read as
marketing affectation on an internal engineering instrument.
**Constraint:** DATUM survives ONLY as internal, non-user-visible code names — CSS token `--datum`,
class `.datum-grid`, sprite `datum-icons.svg`, `sessionStorage['datum-line']`. **Do not rename these
(frozen architecture). Do not reintroduce visible "DATUM" text.**
**Status:** Final.

### D2 — JESA branding retained as endorsement, not decoration
**Decision:** Keep official JESA branding, but only as an **authority/endorsement** signal in
controlled spots (top-bar lockup, title-block/seal strips, footer). Reserve the `--authority` token
(JESA navy) for the seal/title-block ONLY — never interactive, never a hero watermark/splash.
**Why:** Endorsement gives credibility; decoration cheapens it. The governing *standard codes* carry
trust more than a big logo. Reference firms (Bentley/AVEVA) earn authority through discipline.
**Note:** Currently a text-stamp lockup; the official logo asset is pending and JESA trademark usage
must be confirmed before any external production deploy.
**Status:** Final (asset/legal confirmation outstanding).

### D3 — Platform is workflow-driven, not four separate tools
**Decision:** Frame the four modules as **one governed workflow** — Select → Verify → Arrange ·
Reference — reinforced by a numbered spine and matching tool-card indices. "One workflow. Not four
separate tools."
**Why:** A piping engineer's real task spans selection, span verification, and rack arrangement on
the *same line*; presenting four disconnected utilities hid the actual value (a threaded workflow).
**Status:** Final. (The shared Line object that makes the thread literal is the gated Phase 3.)

### D4 — Workspace Home replaced the traditional landing page
**Decision:** Make `/` an **operational Workspace Home** (hero atmosphere → Continue band → workflow
spine → The Board → Standards register), not a marketing landing page.
**Why:** Users return to *do work*, not to read a pitch. Resuming a line and entering a tool are the
primary actions; credibility (standards) supports them. An instrument, not a brochure.
**Status:** Final.

### D5 — Rack Calculator / DXF as an independent module
**Decision:** Treat the Rack Calculator (and its DXF export) as a first-class, independent module in
the Arrangement domain, with its own true-scale schematic pipeline
(`rack_calculator.py` → `rack_geometry.py` → `rack_diagram.py`/`rack_dxf.py`).
**Why:** Rack arrangement is a distinct engineering deliverable (a drawing), not a sub-feature of
support selection. Separating geometry from rendering let SVG and DXF share one approved model
without ever re-deriving or altering the locked sizing math.
**Status:** Final. `rack_calculator.py` formulas are locked — no changes without explicit approval.

### D6 — Hero section redesigned as subtle industrial atmosphere
**Decision:** Hero = minimal, confident copy over a **desaturated plant photo** behind navy scrims +
a faint blueprint grid; the photo is atmosphere only and the message stays primary. No document
codes in the hero (they live in the Standards register); the old rack illustration was removed for a
unified feel; "as little text as possible."
**Why:** The hero must communicate engineering confidence and standards governance in seconds
without reading like a software manual or a SaaS marketing splash. Atmosphere supports the message;
it must never compete with it.
**Status:** Final (refined again in Phase 2.5).

### D7 — Engineering credibility prioritized over marketing language
**Decision:** Copy and visuals lead with **traceability, governance, and reliability**, not
feature-marketing. Credibility comes from standards codes (QW2507-00-PE-STD-00001, Tables 15 & 16,
KS-PE-SPC-0073) surfaced as a first-class Standards & Traceability register.
**Why:** The audience is stress/piping engineers; trust is earned by "every recommendation resolves
to a governing clause, table, and drawing," not by adjectives. A prior decorated-utility redesign
was rejected for exactly this reason.
**Status:** Final.

### D8 — Single interactive accent; strict token layer
**Decision:** `--datum` (teal) is the **only** interactive/active/live accent; `--annotation`
(amber) is for warnings/dimensions-of-interest; verdicts use pass/fail tokens; `--authority` (navy)
is seal-only. No hardcoded hex in CSS rules outside `:root`/`[data-theme="dark"]` (neutral
white/black rgba overlays on dark bands are the one accepted exception).
**Why:** Multiple competing hues made cards feel unengineered/decorative. One disciplined accent
system reads as a coherent instrument and keeps both themes correct.
**Status:** Final.

### D9 — Drafting/title-block visual language + drafting-glyph icons
**Decision:** Outputs are stamped "sheets" (title block + traceability footer); typography is Saira
Semi Condensed (display) + JetBrains Mono (all data/numbers, tabular) + Inter (body); icons are one
coherent drafting-glyph family (`datum-icons.svg`, 20×20, 1.75 stroke, no fills, `currentColor`).
**Why:** Matches how engineers read drawings; differentiates from generic dashboards; aligns with
the Bentley/AVEVA *authority* + Linear *velocity* + Stripe/Notion *typographic discipline* references.
**Status:** Final.

### D10 — Dual theme is mandatory and token-driven
**Decision:** Light ("vellum") and dark ("film") are both first-class, driven entirely by
`:root`/`[data-theme="dark"]`. SVG/DXF/schematics must read correctly in both.
**Why:** Engineers work in varied environments; baked colors would break one theme. Token-driven
theming is also what keeps D8 enforceable.
**Status:** Final.

### D11 — UI work never touches the engine, routes, or `app.js`
**Decision:** All redesign/polish is **markup/CSS/assets only**. Never edit `app.js`, the Python
engine, calculations, or Flask routes for visual work. The `⌘K` palette uses self-contained inline
JS in `_command_palette.html`. Result markup is added *statically* inside `#resultContent`.
**Why:** The engine is mature and covered by 502 tests; presentation changes must not risk it. This
is the boundary that has kept the suite green through the entire redesign.
**Status:** Final (hard constraint).

### D12 — Phase 3 (Line object) is gated behind explicit approval
**Decision:** The shared Line object + cross-tool handoff + unified Result Sheet is fully specified
but **not** to be implemented until the user explicitly says "build." When built, it uses additive
inline scripts + `sessionStorage['datum-line']` only — no `app.js` edits.
**Why:** It is the one piece with a real architectural unknown (cross-tool persistence without
`app.js`); the user wants to approve the approach before implementation.
**Status:** Open/gated — do not start without go-ahead.
