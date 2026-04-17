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

## Current status
Last updated: 2026-04-17 (commit aee51eb)

### Completed
- **PDF row highlighting rewrite** — switched from y-band to x-band approach for rotation=270 pages. `_find_row_rect()` now returns `Rect(hit.x0-1, table_y0, hit.x1+1, table_y1)`.
- **Highlight overflow fix** — table y-bounds detected by searching for column-header anchors ("PIPE SIZE", "NPS", "NB", "DN") within 200 pts of the pipe-size hit. Prevents title-block label false matches (e.g. SC71).
- **Small bore highlight fix** — exact-word match verification via page word list (±3 pt tolerance rejects substring hits like '8"' inside '18"', '40' inside '400'). NPS patterns searched first; DN only as fallback.
- **Format variant coverage** — `_NPS_PATTERNS` now covers: fractional ('3/4"'), decimal ('0.75"'), split-word ('1/2"' for PR01), and no-hyphen ('11/2"' for FRP saddle drawings SC71–SC74).
- **PR01/PR02 isolation pads mapped** — JS-PE-DPS-0380 (page 78) and JS-PE-DPS-0381 (page 79) added to DRAWING_PAGES, DRAWING_INDEX, and DRAWING_SIZE_RANGES.
- **Full drawing index audit** — all support codes verified; CF04/0372 confirmed as SF01 (FRP Thrust Collar) in this PDF revision.

### Known limitations
- **CF04** has no valid drawing in this PDF revision — 0372 is SF01. Clicking CF04 chip produces no PDF. Consider removing CF04 from support_rules.py or showing a "not available" message.
- **SC09** does not exist in the standard (support rules reference "SC06-SC09" but only SC01–SC08 are defined).

### In progress
- Nothing — all three reported PDF issues resolved and pushed.

### Next steps
- Deploy to Railway and verify `/drawing/<ref>` endpoint works in production.
- Decide whether to remove CF04 from support_rules.py or surface a UI message for missing drawings.