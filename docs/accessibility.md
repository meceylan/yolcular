# Accessibility check (step 38)

Colour numbers: `python scripts/check_a11y.py --write` → docs/accessibility_colors.md.
All numbers below were measured with that script on the dark page (ui-redesign: one dark theme, inferno scale, controls with a 3:1 border).

## What was checked and what was changed

| Area | Finding | Fix |
|---|---|---|
| Ramp (inferno 0.15–0.98) in grayscale and deuteranopia / protanopia / tritanopia | Lightness always rises in one direction; neighbouring levels of a 7-level ramp differ by dE2000 ≥ 7.2 and ≥ 8.5 L* in every view | none needed |
| "0 detections" cell | In grayscale it matched the faintest ramp level (0.1 to 3 L* apart) | Ring marker in the cell and in the legend (shape, not colour) |
| Selected-month outline | A single dark outline reached 1.08:1 on dark cells (invisible) | Two-tone ring, dark outside and light inside; at least 4:1 on every cell colour |
| Cells against the page | Faintest ramp colour 1.26:1 (light) and darkest 1.07:1 (dark) against the page | Thin outline in the muted text colour (4.9:1) on cells under 3:1 |
| "No data" hatch | Lines were 1.4:1 against their base | Lines now use the muted text colour (≥ 3:1) |
| Markers (partial month, data gap, estimate outline) | Colour chosen per cell, worst 3.56:1 | none needed |
| Legend | Tick labels overlapped; no text alternative | Ticks only at powers of ten, group label with the scale and the symbols |
| Keyboard | Calendar cells could not be reached | ARIA grid: Tab enters the calendar (one tab stop), arrows move between months, Home/End jump in a year, Ctrl+Home/End first/last month, Enter or Space selects the month to compare |
| Screen readers | Calendar was one image with one label | Every cell has a label (month, value, source, range, data gaps); row and column headers; "Show as table" still gives exact values |
| Tooltip | Mouse only, also announced twice | Shown on keyboard focus too, hidden from screen readers (the cell label carries the same text) |
| Map | Drawing a rectangle needs a pointer | The four labelled coordinate boxes do the same; the map region says so, and "Draw on map" pressed from the keyboard moves focus to the boxes |

## Limits of this check

- The criteria (dE2000 ≥ 6, ≥ 8 L* lightness step, 3:1 for graphics) are our own reading of WCAG 2.1 (1.4.1, 1.4.11) and common practice, not a certification.
- Colour-vision simulation uses the Machado et al. 2009 model; it is a model, not a test with people.
- Screen reader behaviour was not tested with NVDA, JAWS or VoiceOver. The ARIA grid on SVG is correct by specification but support differs between browsers and readers; the table view is the fallback.
- Leaflet's own controls and OpenStreetMap tiles were not changed.

## Step 76 re-check (15 November 2026)

Checked on the live page (same code as `main`) with `scripts/check_a11y.py`, a script pass over every focusable element and a text-contrast pass over every visible text element.

| Area | Result |
|---|---|
| Colour (`check_a11y.py`) | No problems: ramp in grayscale and three colour-vision models, selection ring ≥ 3.9:1, controls and focus ring ≥ 3:1 |
| Text contrast (all visible text, including the Key findings box and the Copy link button) | 0 elements under 4.5:1 |
| Focus order | 48 stops in a logical order: Copy link, month picker, Region, map, area buttons, period, CSV, map layer and Play, Series, table toggle, calendar (one stop), About, footer |
| Focus outline | One global 3 px `:focus-visible` outline (12:1 on the card); the calendar cells use the same outline |
| Names | Every control has a label; the Apply button and the coordinate boxes are labelled (they sit in a closed `details`) |
| Headings | h1, then h2 per section, h3 inside Key findings and About; no skipped levels |
| Text equivalents | Calendar: ARIA grid with a label per cell, and "Show as table". Charts: `role="img"` with a summary label. Map layer: "Most active cells" list and a live readout; map drawing: the four coordinate boxes |

Fixed in this step (small changes, layout untouched):
- Play button: removed `aria-pressed` (the label already switches between "Play" and "Pause"; both together were announced as a confusing "Pause, pressed").
- Esc now hides the tooltip (WCAG 1.4.13) and pauses playback (WCAG 2.2.2).
- Added a "Skip to the calendar" link, visible only on focus, as the first tab stop.

Found, not changed (would alter design or layout):
- The Leaflet map and OpenStreetMap tiles are visual by nature; the text alternatives above carry the same information, but the map itself stays unlabelled per tile.
- Leaflet's zoom buttons and attribution keep Leaflet's own styling.
- The "About the data" heading sits inside the `summary` element; screen readers may read it as one long control name.
- Tab order passes through the Leaflet zoom and attribution links between the map and the area buttons.

NVDA: NVDA ile manuel test yapılmadı (ortam sorunu); renk, klavye sırası, odak, etiket ve başlık hiyerarşisi otomatik/script kontrolleriyle doğrulandı.

(English: no manual NVDA test was done, because of an environment problem; colour, keyboard order, focus, labels and heading hierarchy were verified with automatic/script checks.) Not tested: any screen reader, and real keyboard focus in the in-app browser (focus ring was checked from the style rules, not from a photo of the ring).
