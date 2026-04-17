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
