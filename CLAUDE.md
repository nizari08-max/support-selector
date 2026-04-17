# Support Selector — Project Context

## What this app does
Flask web app that helps stress engineers select appropriate support types for piping systems.

## Key files
- `app.py` — Flask entry point and routes
- `selector.py` — Core logic: `select_support()` function
- `support_rules.py` — Rules engine for support selection
- `drawing_index.py` — Maps support types to drawing references
- `templates/` — HTML templates
- `static/` — CSS/JS assets

## Deployment
- Platform: Railway
- Repo: github.com/nizari08-max/support-selector
- Entry point: `app.py`
- Procfile: `web: python app.py`
- All source files must stay at repo root (not in subdirectories)

## Architecture note
`app.py` calls `from selector import select_support` — selector.py must stay at root.

## UI design system
- **Theme:** Dark precision engineering dashboard (`#0F172A` bg, `#1E293B` panels)
- **Accent colors:** Electric blue `#0EA5E9` (primary), Amber `#F59E0B` (secondary/warnings), Green `#10B981` (success)
- **Fonts:** Rajdhani (UI/labels), JetBrains Mono (codes/numbers), Inter (body) — Google Fonts CDN
- **Layout:** 220px vertical step sidebar + 420px form panel + flex result panel; sidebar hidden ≤1100px; single column ≤960px
- **All colors** defined as CSS variables in `:root` — no hardcoded hex in CSS rules
- **Do not touch `app.js`** when making visual changes — use inline `<script>` in the HTML template instead

## Current status
Last updated: 2026-04-17 (commit 02ffa71)

### Completed
- **PDF row highlighting rewrite** — switched from y-band to x-band approach for rotation=270 pages. `_find_row_rect()` now returns `Rect(hit.x0-1, table_y0, hit.x1+1, table_y1)`.
- **Highlight overflow fix** — table y-bounds detected by searching for column-header anchors ("PIPE SIZE", "NPS", "NB", "DN") within 200 pts of the pipe-size hit. Prevents title-block label false matches (e.g. SC71).
- **Small bore highlight fix** — exact-word match verification via page word list (±3 pt tolerance rejects substring hits like '8"' inside '18"', '40' inside '400'). NPS patterns searched first; DN only as fallback.
- **Format variant coverage** — `_NPS_PATTERNS` now covers: fractional ('3/4"'), decimal ('0.75"'), split-word ('1/2"' for PR01), and no-hyphen ('11/2"' for FRP saddle drawings SC71–SC74).
- **PR01/PR02 isolation pads mapped** — JS-PE-DPS-0380 (page 78) and JS-PE-DPS-0381 (page 79) added to DRAWING_PAGES, DRAWING_INDEX, and DRAWING_SIZE_RANGES.
- **Full drawing index audit** — all support codes verified; CF04/0372 confirmed as SF01 (FRP Thrust Collar) in this PDF revision.
- **DN-to-NPS converter** — inline Quick DN Converter above NPS grid. Engineers enter DN (e.g. 150) and the matching NPS button auto-selects. Unknown DN shows red error; unsupported sizes (DN 32, 65, 125) show amber warning.
- **Support code labels on chips** — each drawing chip shows its support type code (e.g. BP02 / WA01) above the drawing reference number. Implemented via `_REF_TO_CODE` reverse dict and `label_drawings()` in `drawing_index.py`; `drawings_labeled` field added to `SelectionResult` and `/api/select` response.
- **PR01/PR02 size range fix** — `DRAWING_SIZE_RANGES` for 0380/0381 widened to (0.75, 48.0) so isolation pad chips appear correctly across all NPS sizes.
- **Support SVG illustrations redesigned** — all 9 support SVGs redrawn with engineering accuracy (end elevation, viewBox 380×290).
- **MPMS Piping Class selector** — text input above Material dropdown. Entering a valid MPMS class code (e.g. BB3, BD1, BK2) auto-selects the correct material and shows description + rating. Excluded non-metallic classes (BH1/BH2, BL5, BN1, BR1, BT1, BX1–3, BY1/3, BZ1) show a warning. 44 metallic/FRP codes + 11 excluded codes defined in `MPMS_CLASSES` / `MPMS_EXCLUDED` in `app.js`. Piping class echoed in `/api/select` response as `piping_class` field. AUTO badge appears on material field when auto-filled (CSS `::before` on wrapper `[data-auto="true"]`).
- **Full UI redesign — Precision Engineering Dashboard** — dark theme, Rajdhani + JetBrains Mono fonts, 3-column layout with vertical step sidebar, blueprint grid illustration zone, electric blue glows, amber accents. See `PROGRESS.md` for full change list.

### Known limitations
- **CF04** has no valid drawing in this PDF revision — 0372 is SF01. Clicking CF04 chip produces no PDF. Consider removing CF04 from support_rules.py or showing a "not available" message.
- **SC09** does not exist in the standard (support rules reference "SC06-SC09" but only SC01–SC08 are defined).

### In progress
- Nothing — all recent features complete and pushed.

### Next steps
- Deploy to Railway and verify `/drawing/<ref>` endpoint works in production.
- Decide whether to remove CF04 from support_rules.py or surface a UI message for missing drawings.