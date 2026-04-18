# Support Span Calculator — New Feature
**Date:** 2026-04-18

---

## What was added

A fully self-contained **Support Span Calculator** tool accessible at `/span` via a new "SPAN CALC" button in the main navbar.

### Files Created
- **`span_calculator.py`** — Pure Python lookup engine, no Flask imports.
  - `calculate_span(nps, material, service, insulation, code_preference, ss_schedule)` — returns span_m, span_ft, reference, warning, message, thumb_rule_m/ft, chart_data.
  - `get_thumb_rule(nps)` — department thumb rule (1–6": starts 3.5 m, +0.5 m/in; 6–18": starts 6.5 m for 8", +0.25 m/in).
  - `_interp(table, nps)` — linear interpolation between table entries for non-standard sizes.
  - Four tables implemented: A (ASME B31.1 Table 121.5), B (B31.3/Shell DEP CS), C (B31.3 SS Sch 10S), D (ISO 14692 FRP).
- **`templates/span_calculator.html`** — Full standalone page, same navbar/footer/theme as index.html. No new CSS file — page-specific styles in inline `<style>` block.

### Files Modified
- **`app.py`** — Added `from span_calculator import calculate_span`, plus two new routes:
  - `GET /span` → renders `span_calculator.html`
  - `POST /api/span` → calls `calculate_span()`, returns JSON
- **`templates/index.html`** — Added "SPAN CALC" `<a class="nav-tool-link">` button in `.navbar-right`.
- **`static/css/style.css`** — Added `.nav-tool-link` and `.nav-tool-link.active` styles.

## Feature details

### Inputs
- **NPS grid** — same button-style selector as main app (20 sizes: ½" to 48").
- **Material** — CS, LT, SA, SS, DS, SD, AL, AY, CN, FRP (same categories as main app).
- **SS Schedule** — Sch 10S (Table C) vs Standard/Heavy Wall (Table B basis); visible only for SS/DS/SD.
- **Code Reference** — ASME B31.3 / Shell DEP (default) or ASME B31.1; visible only for CS/LT/SA.
- **Fluid Service** — Liquid / Vapor-Gas toggle.
- **Insulation** — Bare / Insulated toggle (hidden for B31.1 which doesn't distinguish).

### Outputs
- Large value card: metres (2 dp) + feet equivalent.
- Reference line (which table/code was used).
- Warning banner for FRP, AL/AY/CN, and B31.1 insulation note.
- Interpolation note when exact NPS not in table.
- **Side-by-side comparison**: ASME reference value vs Dept. Thumb Rule.
- **Inline bar chart**: span vs pipe size for all table entries, selected NPS highlighted.
- Engineering disclaimer at bottom.

### Material routing
| Material | Table used |
|----------|-----------|
| CS, LT, SA + B31.3 | Table B — ASME B31.3 / Shell DEP |
| CS, LT, SA + B31.1 | Table A — ASME B31.1 Table 121.5 |
| SS, DS, SD + Sch 10S | Table C — ASME B31.3 SS Sch 10S |
| SS, DS, SD + Std/Heavy | Table B — CS basis (conservative) |
| FRP | Table D — ISO 14692 (simplified) |
| AL, AY, CN | Table C × 0.85 approximate factor |
| HDPE, PVC etc. | Message — not covered |

---

# App Logo & Favicon — Pipe+Support Icon
**Date:** 2026-04-18

---

## Design Concept
Three-element mark: **blue rounded-square background → white pipe annulus (end elevation) → amber pedestal + base plate.**
Reads instantly as "pipe sitting on a support" at both 16 px and 256 px.
No gradients, no raster images — pure flat SVG geometry.

## Files Created

### `static/favicon.svg` — 32×32 browser-tab icon
- `viewBox="0 0 32 32"`, `width="32" height="32"`
- `<rect width="32" height="32" rx="5" fill="#003DA5"/>` — JESA blue rounded square
- Pipe annulus: outer circle `cx=16 cy=11.5 r=7.5 fill=#FFFFFF`, bore `r=4.5 fill=#003DA5`
- Support post: `rect x=14.25 y=19 w=3.5 h=4 rx=0.5 fill=#F59E0B` (amber)
- Base plate: `rect x=5.5 y=23 w=21 h=4 rx=1.5 fill=#F59E0B` (amber)
- All shapes self-contained, no external deps, scales perfectly

### `static/images/logo_app.svg` — 200×200 full app logo
- Same three-element composition, proportionally scaled
- Outer pipe r=46, bore r=28 with subtle `#1A5AC7` bore-edge ring stroke (3px)
- Amber post `w=18 h=22 rx=3`, base plate `w=132 h=22 rx=8`
- Suitable for About pages, splash screens, documentation

## Files Modified

### `templates/index.html`
1. **Favicon link** added in `<head>` (immediately after `<title>`):
   ```html
   <link rel="icon" type="image/svg+xml"
         href="{{ url_for('static', filename='favicon.svg') }}">
   ```
   Uses Flask `url_for` for correct path resolution in both dev and Railway.

2. **Header logo** replaced `logo_jesa.svg` img with new app icon + JESA text label:
   ```html
   <img src="{{ url_for('static', filename='favicon.svg') }}"
        alt="PSS" class="logo logo-app">
   <span class="logo-label">JESA</span>
   ```
   `logo-app` class prevents the existing `brightness(0) invert(1)` filter from destroying the icon colours.

### `static/css/style.css`
- `.logo-app` — `filter: none; height: 36px; width: 36px; border-radius: 6px;` — overrides `.logo` filter
- `.logo-label` — Outfit 700, 15px, letter-spacing 2.5px, white uppercase — matches navbar brand typographic style

## Verified
- `favicon.svg` + `logo_app.svg` are self-contained, no external refs
- Header brand area reads: [pipe+support icon] JESA | Pipe Support Selector / Engineering Reference Tool
- `filter: none` on `.logo-app` preserves the blue/white/amber palette in the header
- Browser tab replaces the generic PDF icon

---

# Standard PDF Banner — 404 Fix
**Date:** 2026-04-18

---

## Problem
Clicking the "JESA Piping Support Standard" banner returned a 404.
The banner was pointing to `/static/QW2507-00-PE-STD-00001.pdf#page=3`
but the file lives at the **project root**, not inside `static/`.

## Investigation
- `find . -name "QW2507-00-PE-STD-00001.pdf"` → found at `./QW2507-00-PE-STD-00001.pdf`
- No existing Flask route was serving this file (Case B)

## Fix Applied

### `app.py`
- Added `send_from_directory` to the Flask import line
- Added new route `/standard-pdf` that serves the PDF from the project root:
  ```python
  @app.route("/standard-pdf")
  def serve_standard_pdf():
      return send_from_directory(
          os.path.dirname(os.path.abspath(__file__)),
          "QW2507-00-PE-STD-00001.pdf",
          mimetype="application/pdf",
      )
  ```

### `templates/index.html`
- Banner `href` changed from `/static/QW2507-00-PE-STD-00001.pdf#page=3`
  to `/standard-pdf#page=3`
- `target="_blank" rel="noopener"` unchanged — still opens in new tab

## Verified
- `/api/drawing/<ref>` route (drawing chip PDFs) is unaffected — uses `pdf_service.get_drawing_pdf()`
- Banner link resolves to `/standard-pdf#page=3` in rendered HTML

---

# Dark Mode Toggle & Banner Fix
**Date:** 2026-04-18

---

## Files Modified

### `static/css/style.css` — Dark mode support + theme toggle styles

**Global theme transitions (added before reset block):**
- `html { transition: background-color 0.3s ease; }` — smooth page bg change
- `* { transition: background-color 0.3s ease, border-color 0.3s ease, color 0.3s ease; }` — all elements transition on theme switch; does NOT include transform/opacity to preserve animation keyframes
- Existing `@media (prefers-reduced-motion: reduce)` block suppresses all transitions with `!important`

**Dark mode variable block (`[data-theme="dark"]`):**
- `color-scheme: dark` declared on the selector
- Full override of all light-theme CSS variables: `--bg-main #0F172A`, `--bg-card #1E293B`, `--bg-header #002B7A`, `--bg-footer #0A0F1E`
- Accent colors: `--accent-blue #3B82F6`, `--accent-blue-lt #1E3A5F`
- Text: `--text-primary #F1F5F9`, `--text-secondary #94A3B8`, `--text-muted #64748B`
- Border: `--border #334155`
- All legacy alias variables remapped for backward compatibility

**Dark mode component overrides:**
- `.doc-ref-banner` in dark: `--accent-blue-lt` bg, `--border` left border; hover = `#243B5A`
- `.doc-ref-title` / `.doc-ref-arrow` in dark: `--accent-blue` color (was `--bg-header` which is invisible on dark)
- `.pc-feedback.pc-excluded` in dark: translucent red bg, lighter text (#FCA5A5)
- `select option/optgroup` in dark: explicit `--bg-card` background

**Theme toggle button:**
- `.theme-toggle`: transparent bg, no border, 18px emoji font, white color, `border-radius: var(--radius-sm)`, hover = `rgba(255,255,255,0.12)` tint

### `templates/index.html` — Three targeted changes

**1. Early theme restore (`<head>`, before `</head>`):**
- Inline IIFE reads `localStorage.getItem('pss-theme')`; if `'dark'`, sets `data-theme="dark"` on `<html>` synchronously — prevents light-mode flash on dark-mode reload

**2. Theme toggle button (in `.navbar-right`):**
- `<button class="theme-toggle" id="themeToggle">` with `<span id="themeIcon">🌙</span>`
- Light mode active → shows 🌙 (click to go dark); Dark mode active → shows ☀️ (click to go light)

**3. JESA Standard banner:**
- Changed `<div class="doc-ref-banner">` → `<a class="doc-ref-banner" href="/static/QW2507-00-PE-STD-00001.pdf#page=3" target="_blank" rel="noopener">`
- Removed `.doc-ref-sub` subtitle line entirely ("JS-PE-DPS Standard · Revision C · Oct 2025")
- Banner now shows only title "JESA Piping Support Standard" + "VIEW →" arrow

**4. Theme toggle JS (inline `<script>` after existing inline scripts):**
- `applyTheme(theme)`: sets/removes `data-theme` attribute on `<html>`, updates icon text
- On `DOMContentLoaded`, syncs icon with theme already applied by head script
- Click handler: reads current theme, toggles, saves to `localStorage('pss-theme')`, applies new theme
- No external dependencies — vanilla JS only

---

## Functionality Preserved
- All JS element IDs, form fields, Flask routes unchanged
- `app.js` not modified
- No Python files touched
- Light mode is the default; dark mode only when `pss-theme=dark` in localStorage

---

# UI Polish — Typography, Animations & Header/Footer Fixes
**Date:** 2026-04-18

---

## Files Modified

### `static/css/style.css` — Targeted improvements

**Font system:**
- `--font-ui` changed from `'Rajdhani'` to `'Outfit'` — modern geometric, more readable
- `--font-body` changed from `'Inter'` to `'Outfit'` — unified font across all UI text
- `--font-mono` unchanged: `'JetBrains Mono'` for all technical codes/values
- Page title (`.title-main`) bumped to 22px; panel headers to 18px; body text to 13–14px

**Logo fix:**
- `.logo` filter changed from `brightness(10) invert(1)` → `brightness(0) invert(1)` for reliable white conversion against blue header

**Animations (CSS-only, GPU-accelerated, prefers-reduced-motion aware):**
- `navbarSlide` — header slides down from top on page load (0.4s ease-out)
- `cardFadeUp` — sidebar (0s), form panel (0.1s), result panel (0.2s) stagger in on load
- `npsGlow` — selected NPS button pulses a subtle blue ring (2s infinite)
- `badgePop` — APPLICABLE badge scales in with a pop (0.3s, 0.25s delay)
- `chipFadeIn` — drawing chips stagger-fade in via nth-child delays (0.05s–0.54s)
- NPS buttons: `scale(1.05)` hover, `scale(0.95)` active press feel
- Drawing chips: `translateY(-2px)` hover lift + shadow; `scale(0.97)` on click
- `@media (prefers-reduced-motion: reduce)` — disables all animations/transitions

**Footer redesign:**
- Background: `--bg-footer: #002B7A` (dark JESA blue)
- `border-top: 2px solid var(--accent-blue)`
- New layout: `.footer-inner` flexbox with `.footer-brand` (title + dept) and `.footer-year`
- Footer text: "Pipe Support Selector — Engineering Tool" / "Stress Engineering Department · JESA"

**Document reference banner (replaces plain sidebar-meta):**
- `.doc-ref-banner`: `--accent-blue-lt` bg, 4px solid `--bg-header` left border
- Title: "JESA Piping Support Standard" in `--bg-header` bold
- Subtitle: "JS-PE-DPS Standard · Revision C · Oct 2025" in `--text-secondary`
- "VIEW →" right-side arrow label
- Hover: `#DBEAFE` bg, shadow, `translateY(-1px)` lift

**Animation variables added to `:root`:**
- `--anim-fast: 0.15s`, `--anim-med: 0.3s`, `--anim-slow: 0.5s`
- `--bg-footer: #002B7A`

**Step indicator transitions** smoothed to `--anim-med` (0.3s) on color changes

### `templates/index.html` — Targeted HTML updates

- **Google Fonts**: replaced Rajdhani + Inter with `Outfit:wght@300;400;500;600;700`; kept JetBrains Mono
- **Sidebar meta**: replaced plain `sm-tool/sm-std/sm-ver` spans with `.doc-ref-banner` block
- **Footer**: replaced flat single-line footer with structured dark footer (brand + dept + year)
- **Year injection**: inline script sets `#footerYear` to `© YYYY` dynamically

---

## Functionality Preserved
- All JS element IDs, form fields, Flask routes unchanged
- `app.js` not modified
- All animations use `transform` and `opacity` only (GPU-accelerated, no layout thrash)
- `prefers-reduced-motion` respected

---

# UI Refresh — JESA Professional Blue (Light Theme)
**Date:** 2026-04-18

---

## Files Modified

### `static/css/style.css` — Complete theme rewrite (dark → light)

**New color system (all CSS variables in `:root`):**
- `--bg-main: #F0F4F8` — page background (light blue-grey)
- `--bg-card: #FFFFFF` — all panels/cards
- `--bg-header: #003DA5` — JESA corporate blue header
- `--accent-blue: #0057D9` — primary interactive color
- `--accent-blue-lt: #E8F0FE` — hover/selection backgrounds
- `--accent-amber: #F59E0B` — PWHT active, drawing code labels
- `--accent-green: #059669` — APPLICABLE badge
- `--text-primary: #0F172A`, `--text-secondary: #475569`, `--text-muted: #94A3B8`
- `--border: #CBD5E1` — all card/input borders
- `--shadow: 0 2px 8px rgba(0,87,217,0.08)` — blue-tinted shadows
- All legacy aliases remapped to new light values for backward compatibility

**Component-by-component changes:**
- `color-scheme: dark` → `color-scheme: light`; body bg → `--bg-main`
- **Navbar:** `--bg-header` (#003DA5) bg, white text, 3px `#4D8FFF` underline accent
- **Sidebar:** white card, blue active dot, clean borders
- **Form panel:** white card with blue-tinted shadow
- **NPS buttons:** white default, blue selected (solid fill, white text)
- **Toggle pills:** `--bg-main` container; active = solid `--accent-blue` (PWHT = `--accent-amber`)
- **Function grid buttons:** white bg, blue border/bg on hover/selected; light SVG icon colors
- **Submit button:** `--accent-blue` fill, white text, hover = `--accent-blue-dk`
- **DN converter section:** `--accent-blue-lt` tint background
- **Result panel:** white card, 4px solid `--accent-blue` top accent
- **Illustration zone:** `--bg-main` with CSS dot-grid pattern (light blueprint)
- **Drawing chips:** white bg, `--accent-blue` border; hover = solid blue fill, white text
- **Note items:** white bg, amber left border
- **pc-feedback.pc-excluded:** light red warning box (#FEF2F2 bg, red border)
- **Footer/Retry button:** white bg, blue border/text

### `templates/index.html` — Targeted text and SVG fixes

- **Navbar badge:** "PSS v2" → "Engineering Tool"
- **Sidebar meta:** "Table 15 / Table 16" → "JESA Standard"
- **Footer:** removed "Tables 15 & 16" reference
- **Function button SVGs:** all hardcoded dark colors updated to light-theme equivalents
  (pipe fill `#DBEAFE`, stroke `#0057D9`, platform `#E2E8F0`, brackets `#CBD5E1`)
- **Empty state SVG:** dark fills updated to light greys/blues matching new theme

---

## Functionality Preserved
- All JS element IDs, form fields, Flask routes unchanged
- `app.js` not modified
- Responsive at 1920px, 1280px, 768px

---

# UI Redesign — Precision Engineering Dashboard
**Date:** 2026-04-17

---

## Files Modified

### `static/css/style.css` — Complete rewrite

**Color system (all via CSS variables):**
- Background: `--bg-deep: #0F172A` (page), `--bg-panel: #1E293B` (cards), `--bg-surface: #162033` (sidebar)
- Primary: `--blue: #0EA5E9` — buttons, active states, glows, borders
- Secondary: `--amber: #F59E0B` — PWHT active, drawing code labels, N/A state, note border
- Status: `--green: #10B981` (applicable), `--red: #EF4444` (errors)
- Text: `--text-hi: #F8FAFC`, `--text-md: #94A3B8`, `--text-lt: #64748B`
- Borders: `--border: #334155` + blue/amber variants
- Legacy aliases kept for backward compatibility

**Typography (Google Fonts CDN):**
- `--font-ui: 'Rajdhani'` — labels, headings, section titles, button text
- `--font-body: 'Inter'` — descriptions, body text, hints
- `--font-mono: 'JetBrains Mono'` — NPS buttons, drawing refs, DN/PC inputs, summary pills

**Layout:**
- New `.app-shell` (flex row) wraps `.step-sidebar` (220px) + `.main-layout`
- Sidebar hides at <=1100px; stacks single column at <=960px

**Component redesigns:**
- Navbar: dark surface, electric blue underline gradient, Rajdhani font
- NPS buttons: dark elevated cards, monospace font, blue glow on selected
- Material select: dark dropdown; `[data-auto="true"]` shows "AUTO" badge via CSS `::before`
- PWHT toggle: amber theme when "Required" is active
- Function buttons: dark technical cards, blue top-border reveal on hover, blue glow on selected
- Submit button: electric blue fill, sharp corners, Rajdhani uppercase, shimmer on hover
- Result panel: 3px electric blue gradient top border; amber for N/A state
- Illustration zone: dark blueprint grid (CSS `background-image` crosshatch), radial blue overlay
- Drawing chips: dark bg, blue border, amber support-code label (monospace), hover glow
- Note items: amber left border on dark card
- Step sidebar: 3-step vertical indicator — pending/active (glowing blue)/done (solid + checkmark)

---

### `templates/index.html` — Restructured

**New font imports:**
- Rajdhani 500/600/700, JetBrains Mono 400/600, Inter 300-700 (Google Fonts CDN)

**Structural additions:**
- `.app-shell` wraps sidebar + main-layout
- `.step-sidebar` with `#si-1`, `#si-2`, `#si-3` step elements
- `id="materialSelectWrapper"` added to `.select-wrapper` for AUTO badge

**SVG updates (dark theme):**
- Function button icons: pipe fill `#1A3A5C`, stroke `#0EA5E9` (was light indigo — invisible on dark)
- Support platforms: `#0F2940` / `#1A2942`
- Empty state SVG: beams/pipe recolored to `#334155` / `#1E293B`

**Submit label:** changed to "GET SUPPORT TYPE"

**Inline stepper script** (visual only, no functional changes):
- Polls DOM at 250ms to update sidebar step states
- MutationObserver on `#pcFeedback` to set `data-auto` on material wrapper

**All 26 JS-required element IDs verified present.**

---

## Functionality Preserved
- Flask app: imports cleanly, all routes unchanged
- DN converter, piping class auto-fill, drawing PDF click all intact
- `app.js` not modified — all JS functionality preserved
- Responsive at 1920px, 1280px, 768px

---

## Responsive Breakpoints
| Width    | Layout                                  |
|----------|-----------------------------------------|
| >=1100px | Sidebar (220px) + form (420px) + result |
| <=1100px | Sidebar hidden, form (400px) + result   |
| <=960px  | Single column, stacked                  |
| <=560px  | Mobile compact, 5-col NPS grid          |
