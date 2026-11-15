// AI-assisted: generated with Claude (Anthropic)
// Burn calendar: reads precomputed JSON from data/ (see docs/data_contract.md, part C).
// Step 34: area selection (map rectangle or coordinates) sums grid.json cells.
// Step 36: selected month vs median of the same month in other years (incl. partial month, same days).
// Step 35: period (from/to month) filters the calendar, the table and the median years.
// Step 37: CSV download of the selected area and period.
// Step 38: keyboard-navigable calendar (ARIA grid, roving tabindex) with a label on every cell.
// Step 74: fire density layer on the map (maplayer.js): follows the selected month or the period total.
// Step 75: shareable link (share.js): the address follows the view and restores it.
// Step 78: key findings box (findings.js), above the calendar.
// Step 77: climate context box (climate.js), NASA POWER, next to the calendar legend.
"use strict";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const MONTHS_LONG = ["January", "February", "March", "April", "May", "June", "July", "August",
                     "September", "October", "November", "December"];
// Inferno (matplotlib, CC0), sampled from 0.15 to 0.98: perceptually uniform, colour-blind safe,
// monotonic lightness. The near-black start is cut off so the lowest values stay visible on the dark page.
const INFERNO = ["#2b0b57", "#57106e", "#82206c", "#ad305d", "#d24644",
                 "#ee6a24", "#fb9706", "#f9cb35", "#f5f992"];
const SRC_LABEL = { M: "MODIS", V: "VIIRS S-NPP", N: "VIIRS NOAA-20" };
const SERIES_LABEL = { m: "MODIS only (raw)", v: "VIIRS only (raw)", h: "Consistent series" };
const SERIES_HELP = {
  h: "One comparable count for every year. Click a month to compare it with other years.",
  m: "MODIS only, as detected. Click a month to compare it with other years.",
  v: "VIIRS only, as detected (from 2012). Click a month to compare it with other years.",
};
const EXP_DEFAULT = "values before 2012 are rough, and recent values may include some unflagged industrial sources.";
const GAP_MIN = 3;   // days without satellite data before a month is flagged
const SEL_COLOR = "#2b1d2f";   // drawn area on the map: dark plum, apart from the inferno fire colours

const state = {
  region: null, meta: null, monthly: null, grid: null,
  series: "h", table: false,
  bbox: null, full: true,
  cur: null,          // the series currently shown (whole region or selection)
  cmpIdx: null,       // month index chosen for the comparison
  range: { from: 0, to: 0 },   // period: first and last month index shown (inclusive)
  mapMode: "month",   // map layer: "month" (month selected in the calendar) or "period" (period total)
};
const inRange = (k) => k >= state.range.from && k <= state.range.to;
const $ = (id) => document.getElementById(id);

// ---------- colour ----------
function hexToRgb(h) { const n = parseInt(h.slice(1), 16); return [n >> 16, (n >> 8) & 255, n & 255]; }
function rgbToHex(r) { return "#" + r.map((x) => Math.round(x).toString(16).padStart(2, "0")).join(""); }
function ramp() {
  // The page is always dark: "brighter = more" against the dark surface.
  return INFERNO;
}
function colorAt(t) {
  const r = ramp();
  t = Math.min(1, Math.max(0, t));
  const x = t * (r.length - 1), i = Math.floor(x), f = x - i;
  if (i >= r.length - 1) return r[r.length - 1];
  const a = hexToRgb(r[i]), b = hexToRgb(r[i + 1]);
  return rgbToHex(a.map((v, k) => v + (b[k] - v) * f));
}
// Log scale: counts span 0 to ~20 000 per month.
function scaleFor(values) {
  const pos = values.filter((v) => v != null && v > 0);
  const max = pos.length ? Math.max(...pos) : 10;
  const min = pos.length ? Math.min(...pos) : 1;
  const lo = Math.log10(min), hi = Math.max(Math.log10(max), lo + 1);
  return { max, min, lo, hi, t: (v) => (Math.log10(Math.max(v, min)) - lo) / (hi - lo) };
}
// Ink that stays visible on top of a given cell fill (markers on dark or light cells).
function lumOf(hex) {
  const [r, g, b] = hexToRgb(hex).map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
function contrastOf(a, b) {
  const la = lumOf(a), lb = lumOf(b);
  return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
}
function inkOn(fill) {
  if (!fill || fill[0] !== "#") return cssVar("--ink");
  return lumOf(fill) > 0.25 ? "#1d1f23" : "#ffffff";
}
const cssVar = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const fmt = (v) => (v == null ? "no data" : Math.round(v).toLocaleString("en-US"));
const fmtDeg = (v) => (+v).toFixed(2);
const monthName = (ym) => `${MONTHS_LONG[+ym.slice(5) - 1]} ${ym.slice(0, 4)}`;

// ---------- data ----------
async function getJSON(path) {
  const r = await fetch(path, { cache: "no-cache" });
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return r.json();
}

// Clear message when a data file cannot be loaded (step 58).
function showLoadError(err, what) {
  const box = $("load-error");
  const local = location.protocol === "file:";
  box.textContent = local
    ? "The data could not be loaded because the page was opened as a file. Start a local web server (python -m http.server 8000 --directory web) and open http://localhost:8000."
    : `The data for ${what} could not be loaded (${err.message}). Check your internet connection and reload the page.`;
  box.hidden = false;
}
const regionNames = {};

async function loadRegion(id) {
  $("cards-ctx").textContent = `Loading ${regionNames[id] || "data"}…`;
  document.querySelector("main").setAttribute("aria-busy", "true");
  if (typeof heatSetPlaying === "function" && heat.playing) heatSetPlaying(false);
  const [meta, monthly, grid] = await Promise.all([
    getJSON(`data/${id}/meta.json`), getJSON(`data/${id}/monthly.json`), getJSON(`data/${id}/grid.json`)]);
  Object.assign(state, { region: id, meta, monthly, grid });
  if (typeof loadClimate === "function") await loadClimate(id);
  if (!meta.harmonized && state.series === "h" && !state._userPicked) state.series = "m";
  if (meta.harmonized && !state._userPicked) state.series = "h";
  $("series").value = state.series;
  $("series").querySelector('option[value="h"]').textContent =
    meta.harmonized ? "Consistent series (recommended)" : "Combined (raw, sensor switch 2012)";
  $("about-filters").textContent = meta.filters || "";
  $("exp-banner").hidden = meta.quality !== "experimental";
  $("exp-banner").lastChild.textContent = " " + (meta.quality_note || EXP_DEFAULT);
  $("ack").textContent = meta.acknowledgment || "";
  state.cmpIdx = monthly.months.indexOf(meta.last_complete_month);
  if (state.cmpIdx < 0) state.cmpIdx = monthly.months.length - 1;
  state.range = { from: 0, to: monthly.months.length - 1 };
  state.focusIdx = null;
  state.mapMode = "month";
  if (typeof heat !== "undefined") { heat.pinned = false; heat.hl = null; }
  fillPeriodSelects();
  fillCompareSelect();
  setupMap();
  setBbox(regionBbox(), true);
  $("load-error").hidden = true;
  document.querySelector("main").removeAttribute("aria-busy");
}

const regionBbox = () => ({ ...state.meta.bbox });

// ---------- selection (step 34) ----------
function cellCenter(i, j, cell) { return [(i + 0.5) * cell - 90, (j + 0.5) * cell - 180]; }

function selectCells(b) {
  const cell = state.grid.cell_deg;
  const inside = (c) => {
    const [la, lo] = cellCenter(c.i, c.j, cell);
    return la >= b.south && la <= b.north && lo >= b.west && lo <= b.east;
  };
  return { cells: state.grid.cells.filter(inside),
           mtdCells: state.grid.mtd ? state.grid.mtd.cells.filter(inside) : [] };
}

// Ratio of the country-level uncertainty band, applied to a sub-area (same coefficients).
function factors(M, k) {
  if (!M.h_lo || !M.h[k]) return [1, 1];
  return [M.h_lo[k] / M.h[k], M.h_hi[k] / M.h[k]];
}

function seriesFor(b, full) {
  const M = state.monthly;
  if (full) return { ...M, full: true };
  const n = M.months.length;
  const { cells, mtdCells } = selectCells(b);
  const h = Array(n).fill(0), m = Array(n).fill(0), v = M.v.map((x) => (x == null ? null : 0));
  for (const c of cells) for (const [k, hh, mm, vv] of c.d) { h[k] += hh; m[k] += mm; if (v[k] != null && vv != null) v[k] += vv; }
  const S = { ...M, full: false, h: h.map((x) => Math.round(x * 10) / 10), m, v, out_of_range: null };
  S.h_lo = S.h.map((x, k) => Math.round(x * factors(M, k)[0] * 10) / 10);
  S.h_hi = S.h.map((x, k) => Math.round(x * factors(M, k)[1] * 10) / 10);
  if (M.mtd) {
    const T = M.mtd, ny = T.years.length;
    const th = Array(ny).fill(0), tm = Array(ny).fill(0), tv = T.v.map((x) => (x == null ? null : 0));
    for (const c of mtdCells) for (const [k, hh, mm, vv] of c.d) { th[k] += hh; tm[k] += mm; if (tv[k] != null && vv != null) tv[k] += vv; }
    S.mtd = { ...T, h: th.map((x) => Math.round(x * 10) / 10), m: tm, v: tv };
    S.mtd.h_lo = S.mtd.h.map((x, k) => Math.round(x * factors(T, k)[0] * 10) / 10);
    S.mtd.h_hi = S.mtd.h.map((x, k) => Math.round(x * factors(T, k)[1] * 10) / 10);
  }
  S.nCells = cells.length;
  return S;
}

function clampToRegion(b) {
  const R = regionBbox();
  return { south: Math.max(R.south, Math.min(b.south, b.north)), north: Math.min(R.north, Math.max(b.south, b.north)),
           west: Math.max(R.west, Math.min(b.west, b.east)), east: Math.min(R.east, Math.max(b.west, b.east)) };
}

function setBbox(b, full = false) {
  b = clampToRegion(b);
  const R = regionBbox();
  full = full || (b.south <= R.south && b.north >= R.north && b.west <= R.west && b.east >= R.east);
  const S = seriesFor(b, full);
  const status = $("bbox-status");
  if (!full && S.nCells === 0) {
    status.textContent = "No grid cell centre is inside this rectangle. Make it larger (at least 0.25° on each side).";
    return;
  }
  state.bbox = b; state.full = full; state.cur = S;
  ["north", "south", "west", "east"].forEach((k) => { $(`b-${k}`).value = fmtDeg(b[k]); });
  status.textContent = full ? `Whole region: ${state.meta.name_en}.`
    : `Selected ${S.nCells} grid cells: ${fmtDeg(b.south)}–${fmtDeg(b.north)}° N, ${fmtDeg(b.west)}–${fmtDeg(b.east)}° E.`;
  drawSelectionOnMap();
  render();
}

// ---------- map ----------
let map = null, regionLayer = null, selLayer = null;
function setupMap() {
  const R = regionBbox();
  const bounds = [[R.south, R.west], [R.north, R.east]];
  if (!window.L) { $("map").textContent = "Map could not be loaded; use the coordinate boxes."; return; }
  if (!map) {
    map = L.map("map", { zoomSnap: 0.25, scrollWheelZoom: false, keyboard: true });
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 12, minZoom: 3,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);
    setupDrawing();
    if (typeof heatInit === "function") heatInit(map);
  }
  if (regionLayer) regionLayer.remove();
  regionLayer = L.rectangle(bounds, { color: "#65546b", weight: 1, dashArray: "4 4", fill: false, interactive: false }).addTo(map);
  // Fit after layout settles (the container may still be resizing on first load).
  requestAnimationFrame(() => { map.invalidateSize(); map.fitBounds(bounds, { padding: [8, 8] }); });
}

function drawSelectionOnMap() {
  if (!map) return;
  if (selLayer) { selLayer.remove(); selLayer = null; }
  if (state.full) return;
  // Show the selection snapped to the grid cells that are actually counted.
  const cell = state.grid.cell_deg, { cells } = selectCells(state.bbox);
  if (!cells.length) return;
  let s = 90, n = -90, w = 180, e = -180;
  for (const c of cells) {
    const la = c.i * cell - 90, lo = c.j * cell - 180;
    s = Math.min(s, la); n = Math.max(n, la + cell); w = Math.min(w, lo); e = Math.max(e, lo + cell);
  }
  selLayer = L.rectangle([[s, w], [n, e]], { color: SEL_COLOR, weight: 2, fillOpacity: 0.08, interactive: false }).addTo(map);
}

function setupDrawing() {
  const btn = $("draw-btn"), el = map.getContainer();
  let drawing = false, start = null, temp = null;
  const stop = () => {
    drawing = false; start = null;
    btn.textContent = "Draw on map";
    el.classList.remove("drawing"); el.style.touchAction = "";
    map.dragging.enable();
  };
  btn.addEventListener("click", (ev) => {
    if (drawing) { stop(); return; }
    if (ev.detail === 0) {   // activated from the keyboard: drawing needs a pointer
      $("bbox-status").textContent = "Drawing needs a mouse or touch. Type the four coordinates and press Apply.";
      $("b-north").focus();
      return;
    }
    drawing = true;
    btn.textContent = "Cancel drawing";
    el.classList.add("drawing"); el.style.touchAction = "none";
    map.dragging.disable();
    $("bbox-status").textContent = "Press and drag on the map to draw a rectangle.";
  });
  const ll = (ev) => map.mouseEventToLatLng(ev);
  el.addEventListener("pointerdown", (ev) => {
    if (!drawing) return;
    ev.preventDefault(); ev.stopPropagation();
    el.setPointerCapture(ev.pointerId);
    start = ll(ev);
    temp = L.rectangle([start, start], { color: SEL_COLOR, weight: 2, dashArray: "5 4", fillOpacity: 0.05, interactive: false }).addTo(map);
  });
  el.addEventListener("pointermove", (ev) => { if (drawing && start && temp) temp.setBounds([start, ll(ev)]); });
  el.addEventListener("pointerup", (ev) => {
    if (!drawing || !start) return;
    const end = ll(ev), a = start;
    if (temp) { temp.remove(); temp = null; }
    stop();
    setBbox({ south: Math.min(a.lat, end.lat), north: Math.max(a.lat, end.lat),
              west: Math.min(a.lng, end.lng), east: Math.max(a.lng, end.lng) });
  });
}

// ---------- period (step 35) ----------
const ymParts = (idx) => { const ym = state.monthly.months[idx]; return [ym.slice(0, 4), String(+ym.slice(5))]; };

function fillPeriodSelects() {
  const months = state.monthly.months;
  const years = [...new Set(months.map((ym) => ym.slice(0, 4)))];
  const yopts = years.map((y) => `<option value="${y}">${y}</option>`).join("");
  const mopts = MONTHS_LONG.map((m, k) => `<option value="${k + 1}">${m}</option>`).join("");
  for (const p of ["from", "to"]) { $(`${p}-year`).innerHTML = yopts; $(`${p}-month`).innerHTML = mopts; }
  syncPeriodSelects();
}

function syncPeriodSelects() {
  for (const p of ["from", "to"]) {
    const [y, m] = ymParts(state.range[p]);
    $(`${p}-year`).value = y; $(`${p}-month`).value = m;
  }
}

// Index of a month in the data; months outside the data are clamped to the nearest end.
function monthIndex(y, m) {
  const months = state.monthly.months, key = `${y}-${String(m).padStart(2, "0")}`;
  const i = months.indexOf(key);
  return i >= 0 ? i : (key < months[0] ? 0 : months.length - 1);
}

// Keep the month used for the comparison inside the period.
function ensureCompareMonth() {
  const { from, to } = state.range;
  if (state.cmpIdx >= from && state.cmpIdx <= to) return;
  let k = to;
  while (k > from && state.monthly.partial[k]) k--;   // prefer the last complete month
  state.cmpIdx = k;
}

function onPeriodChange(which) {
  const months = state.monthly.months, notes = [];
  let a = monthIndex($("from-year").value, $("from-month").value);
  let b = monthIndex($("to-year").value, $("to-month").value);
  const asked = (p) => `${$(`${p}-year`).value}-${String($(`${p}-month`).value).padStart(2, "0")}`;
  if (months[a] !== asked("from") || months[b] !== asked("to"))
    notes.push(`Data cover ${monthName(months[0])} to ${monthName(months[months.length - 1])}; the period was adjusted.`);
  if (a > b) {
    if (which === "from") b = a; else a = b;
    notes.push("The start cannot be after the end; the other end was moved to match.");
  }
  state.range = { from: a, to: b };
  state.mapMode = "period";   // a chosen period shows its total on the map
  if (heat.playing) heatSetPlaying(false);
  syncPeriodSelects();
  $("period-note").textContent = notes.join(" ");
  ensureCompareMonth();
  fillCompareSelect();
  state.focusIdx = null;
  render();
}

function resetPeriod() {
  state.range = { from: 0, to: state.monthly.months.length - 1 };
  state.mapMode = "month";
  if (heat.playing) heatSetPlaying(false);
  syncPeriodSelects();
  $("period-note").textContent = "";
  ensureCompareMonth();
  fillCompareSelect();
  state.focusIdx = null;
  render();
}

// ---------- calendar rows ----------
function rows() {
  const M = state.cur, s = state.series, byYear = new Map();
  M.months.forEach((ym, idx) => {
    if (!inRange(idx)) return;
    const y = +ym.slice(0, 4), m = +ym.slice(5) - 1;
    if (!byYear.has(y)) byYear.set(y, Array(12).fill(null));
    byYear.get(y)[m] = { ym, idx, value: M[s][idx], src: M.src[idx], partial: M.partial[idx] };
  });
  return [...byYear.entries()].sort((a, b) => a[0] - b[0]).map(([year, cells]) => ({ year, cells }));
}

// ---------- render ----------
function render() {
  const { meta } = state;
  const notice = $("notice");
  notice.hidden = meta.harmonized && state.series === "h";
  notice.className = "notice";
  notice.textContent = "Raw counts from one sensor: compare years only within this series." +
    (meta.harmonized ? "" : " Industrial heat sources and low-confidence detections are still included.");
  $("series-help").textContent = SERIES_HELP[state.series];
  drawCalendar();
  drawLegend();
  drawCompare();
  drawSummary();
  drawCharts();
  if (state.table) drawTable();
  if (typeof heatUpdate === "function") heatUpdate();
  if (typeof drawFindings === "function") drawFindings();
  if (typeof drawClimate === "function") drawClimate();
  if (typeof shareWrite === "function") shareWrite();
}

function drawCalendar() {
  const data = rows();
  const all = data.flatMap((r) => r.cells.filter(Boolean).map((c) => c.value));
  const sc = scaleFor(all);
  state.scale = sc;
  const host = $("calendar");
  const surfaceHex = cssVar("--surface");
  const W = Math.max(320, host.clientWidth || 600);
  const labelW = 40, headH = 18;
  const cw = (W - labelW) / 12, ch = Math.max(14, Math.min(20, cw * 0.3));
  const H = headH + data.length * ch;
  const NS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(NS, "svg");
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.setAttribute("role", "grid");
  svg.setAttribute("aria-rowcount", data.length + 1);
  svg.setAttribute("aria-colcount", 13);
  svg.setAttribute("aria-label",
    `Burn calendar, ${SERIES_LABEL[state.series]} detections per month, ${data[0].year} to ${data[data.length - 1].year}. ` +
    `Highest month: ${fmt(sc.max)}. Arrow keys move between months, Enter selects a month to compare. "Show as table" gives exact values.`);
  // Roving tabindex: exactly one cell is in the Tab order.
  const visible = data.flatMap((r) => r.cells.filter(Boolean).map((c) => c.idx));
  if (state.focusIdx == null || !visible.includes(state.focusIdx))
    state.focusIdx = visible.includes(state.cmpIdx) ? state.cmpIdx : visible[0];

  const defs = document.createElementNS(NS, "defs");
  defs.innerHTML = `<pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <rect width="6" height="6" fill="${cssVar("--zero")}"/><line x1="0" y1="0" x2="0" y2="6" stroke="${cssVar("--muted")}" stroke-width="1.5"/></pattern>`;
  svg.appendChild(defs);

  const headRow = document.createElementNS(NS, "g");
  headRow.setAttribute("role", "row"); headRow.setAttribute("aria-rowindex", 1);
  MONTHS.forEach((m, k) => {
    const t = document.createElementNS(NS, "text");
    t.setAttribute("role", "columnheader"); t.setAttribute("aria-label", MONTHS_LONG[k]);
    t.setAttribute("x", labelW + k * cw + cw / 2); t.setAttribute("y", 12);
    t.setAttribute("text-anchor", "middle"); t.textContent = cw < 34 ? m[0] : m;
    headRow.appendChild(t);
  });
  svg.appendChild(headRow);
  data.forEach((row, r) => {
    const y = headH + r * ch;
    const g = document.createElementNS(NS, "g");
    g.setAttribute("role", "row"); g.setAttribute("aria-rowindex", r + 2);
    svg.appendChild(g);
    const t = document.createElementNS(NS, "text");
    t.setAttribute("role", "rowheader");
    t.setAttribute("x", labelW - 6); t.setAttribute("y", y + ch / 2 + 4);
    t.setAttribute("text-anchor", "end"); t.textContent = row.year;
    g.appendChild(t);
    row.cells.forEach((c, k) => {
      if (!c) return;
      const rect = document.createElementNS(NS, "rect");
      const x0 = labelW + k * cw;
      rect.setAttribute("x", x0); rect.setAttribute("y", y);
      rect.setAttribute("width", cw); rect.setAttribute("height", ch);
      rect.setAttribute("rx", 3);
      rect.setAttribute("class", "cell" + (c.idx === state.cmpIdx ? " selected" : ""));
      rect.setAttribute("role", "gridcell");
      rect.setAttribute("aria-colindex", k + 2);
      rect.setAttribute("aria-selected", String(c.idx === state.cmpIdx));
      rect.setAttribute("tabindex", c.idx === state.focusIdx ? "0" : "-1");
      rect.setAttribute("aria-label", cellLabel(c.idx));
      let fill;
      if (c.value == null) fill = "url(#hatch)";
      else if (c.value === 0) fill = cssVar("--zero");
      else fill = colorAt(sc.t(c.value));
      rect.setAttribute("fill", fill);
      rect.dataset.idx = c.idx;
      // Cells that would blend into the page (contrast under 3:1) get a thin outline (WCAG 1.4.11).
      if (fill[0] !== "#" || contrastOf(fill, surfaceHex) < 3) rect.classList.add("lowc");
      g.appendChild(rect);
      const ink = inkOn(fill);
      if (c.value === 0) {   // ring = "nothing detected"; also tells 0 apart from the faintest colour in grayscale
        const ring0 = document.createElementNS(NS, "circle");
        ring0.setAttribute("cx", x0 + cw / 2); ring0.setAttribute("cy", y + ch / 2); ring0.setAttribute("r", 2.5);
        ring0.setAttribute("fill", "none"); ring0.setAttribute("stroke", ink); ring0.setAttribute("stroke-width", 1.3);
        ring0.setAttribute("pointer-events", "none"); ring0.setAttribute("aria-hidden", "true");
        g.appendChild(ring0);
      }
      if (c.partial) {   // top-right corner: partial (current) month
        const tri = document.createElementNS(NS, "path");
        tri.setAttribute("d", `M${x0 + cw - 9},${y + 1} L${x0 + cw - 1},${y + 1} L${x0 + cw - 1},${y + 9} Z`);
        tri.setAttribute("fill", ink); tri.setAttribute("pointer-events", "none"); tri.setAttribute("aria-hidden", "true");
        g.appendChild(tri);
      }
      if (isGap(c)) {    // bottom-left corner: satellite data missing on several days
        const tri = document.createElementNS(NS, "path");
        tri.setAttribute("d", `M${x0 + 1},${y + ch - 9} L${x0 + 1},${y + ch - 1} L${x0 + 9},${y + ch - 1} Z`);
        tri.setAttribute("fill", ink); tri.setAttribute("pointer-events", "none"); tri.setAttribute("aria-hidden", "true");
        g.appendChild(tri);
      }
      if (isEstimate(c) && c.value) {   // dashed outline: estimated month
        const o = document.createElementNS(NS, "rect");
        o.setAttribute("x", x0 + 2.5); o.setAttribute("y", y + 2.5);
        o.setAttribute("width", Math.max(0, cw - 5)); o.setAttribute("height", Math.max(0, ch - 5));
        o.setAttribute("rx", 2); o.setAttribute("fill", "none"); o.setAttribute("stroke", ink);
        o.setAttribute("stroke-width", 1.2); o.setAttribute("stroke-dasharray", "3 2");
        o.setAttribute("pointer-events", "none"); o.setAttribute("aria-hidden", "true");
        g.appendChild(o);
      }
    });
  });
  const ring = document.createElementNS(NS, "g");
  ring.setAttribute("id", "selring"); ring.setAttribute("aria-hidden", "true"); ring.setAttribute("pointer-events", "none");
  ring.innerHTML = '<rect class="ring-out" rx="4"/><rect class="ring-in" rx="3"/>';
  svg.appendChild(ring);
  host.replaceChildren(svg);
  attachHover(svg);
  moveRing(state.cmpIdx);
}

// Two-tone ring (dark outside, light inside) around the month chosen for the comparison.
function moveRing(idx) {
  const ring = $("selring");
  if (!ring) return;
  const cell = document.querySelector(`#calendar rect.cell[data-idx="${idx}"]`);
  ring.style.display = cell ? "" : "none";
  if (!cell) return;
  const x = +cell.getAttribute("x"), y = +cell.getAttribute("y"), w = +cell.getAttribute("width"), h = +cell.getAttribute("height");
  const set = (el, dx, dy, dw, dh) => { el.setAttribute("x", x + dx); el.setAttribute("y", y + dy); el.setAttribute("width", Math.max(1, w + dw)); el.setAttribute("height", Math.max(1, h + dh)); };
  set(ring.querySelector(".ring-out"), -1, -1, 2, 2);
  set(ring.querySelector(".ring-in"), 1.75, 1.75, -3.5, -3.5);
}

function isEstimate(c) { return state.meta.harmonized && state.series === "h" && c.src !== "V"; }
function isGap(c) {
  // gap_days counts missing days of the satellite the series uses that month.
  const g = (state.cur.gap_days || [])[c.idx] || 0;
  if (g < GAP_MIN) return false;
  if (state.series === "h") return true;
  return state.series === "v" ? c.src !== "M" : c.src === "M";
}

function tooltipHTML(idx) {
  const M = state.cur, ym = M.months[idx];
  const [y, m] = ym.split("-");
  const lines = [`<div><b>${MONTHS[+m - 1]} ${y}</b>${M.partial[idx] ? ` <span class="t-muted">(partial: days 1–${M.mtd ? M.mtd.through_day : "?"})</span>` : ""}</div>`];
  lines.push(`<div>${SERIES_LABEL[state.series]}: <b>${fmt(M[state.series][idx])}</b></div>`);
  if (state.series !== "m") lines.push(`<div class="t-muted">MODIS: ${fmt(M.m[idx])}</div>`);
  if (state.series !== "v") lines.push(`<div class="t-muted">VIIRS: ${fmt(M.v[idx])}</div>`);
  const src = M.src[idx];
  if (state.meta.harmonized && state.series === "h") {
    const how = { V: "Measured: VIIRS S-NPP",
                  M: "Estimate: MODIS × monthly factor",
                  N: `Estimate: VIIRS NOAA-20 × ${state.meta.viirs_switch.k_n20}` }[src];
    lines.push(`<div>Source: ${how}</div>`);
    if (src !== "V" && M.h_lo) lines.push(`<div>Likely range: ${fmt(M.h_lo[idx])} – ${fmt(M.h_hi[idx])}</div>`);
    if (M.out_of_range && M.out_of_range[idx])
      lines.push(`<div>Fire activity above the tested level: probably overestimated, wide range.</div>`);
    if (!M.full && src === "M")
      lines.push(`<div class="t-muted">Small areas: estimates before 2012 are rough.</div>`);
  } else {
    lines.push(`<div class="t-muted">VIIRS satellite this month: ${src === "M" ? "none (before Feb 2012)" : SRC_LABEL[src]}</div>`);
  }
  const g = (M.gap_days || [])[idx] || 0;
  if (g) lines.push(`<div${g >= GAP_MIN ? "" : ' class="t-muted"'}>${g} day${g > 1 ? "s" : ""} without satellite data${g >= GAP_MIN ? "; value likely too low" : ""}.</div>`);
  return lines.join("");
}

// Plain-text description of a month, used as the screen-reader label of its cell.
function cellLabel(idx) {
  const box = document.createElement("div");
  box.innerHTML = tooltipHTML(idx);
  return [...box.children].map((c) => c.textContent.trim().replace(/\s+/g, " ")).join(". ") + ".";
}

// Choose the month for the comparison cards without redrawing (keeps keyboard focus).
function selectMonth(idx) {
  state.cmpIdx = idx;
  $("compare-month").value = String(idx);
  document.querySelectorAll("#calendar rect.cell").forEach((r) => {
    const on = +r.dataset.idx === idx;
    r.classList.toggle("selected", on);
    r.setAttribute("aria-selected", String(on));
  });
  moveRing(idx);
  drawCompare();
  drawLine();
  state.mapMode = "month";
  if (typeof drawFindings === "function") drawFindings();
  if (typeof drawClimate === "function") drawClimate();
  if (typeof heatUpdate === "function") heatUpdate();
  if (typeof shareWrite === "function") shareWrite();
}

function attachHover(svg) {
  const tip = $("tooltip");
  let last = null;
  const cellOf = (e) => (e.target.closest ? e.target.closest("rect.cell") : null);
  const placeTip = (el, x, y) => {
    tip.innerHTML = tooltipHTML(+el.dataset.idx);
    tip.hidden = false;
    const pad = 14, tw = tip.offsetWidth, th = tip.offsetHeight;
    let px = x + pad, py = y + pad;
    if (px + tw > window.innerWidth - 8) px = x - tw - pad;
    if (py + th > window.innerHeight - 8) py = y - th - pad;
    tip.style.left = Math.max(4, px) + "px"; tip.style.top = Math.max(4, py) + "px";
  };
  svg.addEventListener("pointermove", (e) => {
    const el = cellOf(e);
    if (last && last !== el) last.classList.remove("hover");
    if (!el) { tip.hidden = true; last = null; return; }
    el.classList.add("hover"); last = el;
    placeTip(el, e.clientX, e.clientY);
  });
  svg.addEventListener("pointerleave", () => { tip.hidden = true; if (last) last.classList.remove("hover"); last = null; });
  svg.addEventListener("click", (e) => {
    const el = cellOf(e);
    if (!el) return;
    state.focusIdx = +el.dataset.idx;
    selectMonth(+el.dataset.idx);
  });

  // Keyboard: show the same details as the mouse tooltip when a cell gets focus.
  svg.addEventListener("focusin", (e) => {
    const el = cellOf(e);
    if (!el) return;
    const r = el.getBoundingClientRect();
    placeTip(el, r.left, r.bottom);
  });
  svg.addEventListener("focusout", () => { tip.hidden = true; });
  svg.addEventListener("keydown", (e) => {
    const el = cellOf(e);
    if (!el) return;
    const idx = +el.dataset.idx, { from, to } = state.range;
    const first = (k) => Math.max(from, k);
    let next = null;
    switch (e.key) {
      case "ArrowRight": next = idx + 1; break;
      case "ArrowLeft": next = idx - 1; break;
      case "ArrowDown": next = idx + 12; break;
      case "ArrowUp": next = idx - 12; break;
      case "Home": next = e.ctrlKey ? from : first(idx - (+state.monthly.months[idx].slice(5) - 1)); break;
      case "End": next = e.ctrlKey ? to : Math.min(to, idx + (12 - +state.monthly.months[idx].slice(5))); break;
      case "Enter": case " ": e.preventDefault(); selectMonth(idx); return;
      default: return;
    }
    e.preventDefault();
    if (next < from || next > to) return;
    const target = svg.querySelector(`rect.cell[data-idx="${next}"]`);
    if (!target) return;
    el.setAttribute("tabindex", "-1");
    target.setAttribute("tabindex", "0");
    state.focusIdx = next;
    target.focus();
  });
}

function drawLegend() {
  const sc = state.scale, L = $("legend");
  const stops = Array.from({ length: 11 }, (_, i) => `${colorAt(i / 10)} ${i * 10}%`).join(",");
  const frac = (v) => (Math.log10(v) - sc.lo) / (sc.hi - sc.lo);
  const vals = [];
  for (let p = Math.floor(sc.lo); p <= Math.ceil(sc.hi); p++) if (frac(10 ** p) > 0.04 && frac(10 ** p) < 0.96) vals.push(10 ** p);
  const apart = (v) => vals.every((u) => Math.abs(frac(u) - frac(v)) > 0.16);
  const short = (v) => (v >= 1000 ? `${+(v / 1000).toFixed(1)}k` : `${Math.round(v)}`);
  const tickHTML = [sc.min, ...vals, sc.max].filter((v, i, a) => (i > 0 && i < a.length - 1) || apart(v)).map((v) => {
    const left = ((Math.log10(v) - sc.lo) / (sc.hi - sc.lo)) * 100;
    return `<span style="position:absolute;left:${left}%;transform:translateX(-${left}%)">${short(v)}</span>`;
  }).join("");
  const partial = state.cur.partial.some((p, k) => p && inRange(k));
  L.setAttribute("role", "group");
  L.setAttribute("aria-label", `Colour legend. Colour scale from ${fmt(sc.min)} (darkest) to ${fmt(sc.max)} (brightest) detections per month, log scale. A ring marks 0 detections, hatching marks no data.`);
  L.innerHTML = `
    <div class="ramp">
      <span>Fire detections per month<br><span class="t-muted">log scale</span></span>
      <div class="bar" style="background:linear-gradient(90deg,${stops})"></div>
      <div class="ticks" style="position:relative;height:1.2em">${tickHTML}</div>
    </div>
    <span class="key"><svg width="14" height="14" aria-hidden="true"><rect x="0.5" y="0.5" width="13" height="13" rx="3" fill="${cssVar("--zero")}" stroke="${cssVar("--muted")}"/><circle cx="7" cy="7" r="2.5" fill="none" stroke="${inkOn(cssVar("--zero"))}" stroke-width="1.3"/></svg>0 detections</span>
    <span class="key"><svg width="14" height="14" aria-hidden="true"><rect x="0.5" y="0.5" width="13" height="13" rx="3" fill="url(#hatch)" stroke="${cssVar("--muted")}"/></svg>No data</span>
    ${partial ? `<span class="key"><svg width="14" height="14" aria-hidden="true"><path d="M5,0 L14,0 L14,9 Z" fill="${cssVar("--ink")}"/></svg>Partial month (days 1–${state.cur.mtd ? state.cur.mtd.through_day : "?"})</span>` : ""}
    ${state.meta.harmonized && state.series === "h" ? `<span class="key"><svg width="14" height="14" aria-hidden="true"><rect width="14" height="14" rx="3" fill="${colorAt(0.5)}"/><rect x="2.5" y="2.5" width="9" height="9" rx="2" fill="none" stroke="${inkOn(colorAt(0.5))}" stroke-width="1.2" stroke-dasharray="3 2"/></svg><span>Estimate<br><span class="t-muted">before Feb 2012, from Nov 2026</span></span></span>` : ""}
    <span class="key"><svg width="14" height="14" aria-hidden="true"><rect x="0.5" y="0.5" width="13" height="13" rx="3" fill="${cssVar("--zero")}" stroke="${cssVar("--line")}"/><path d="M1,5 L1,13 L9,13 Z" fill="${cssVar("--ink")}"/></svg>${GAP_MIN}+ days missing (likely too low)</span>`;
}

function drawTable() {
  const data = rows();
  const head = `<tr><th scope="col">Year</th>${MONTHS.map((m) => `<th scope="col">${m}</th>`).join("")}<th scope="col">Total</th></tr>`;
  const body = data.map((r) => {
    let tot = 0;
    const tds = r.cells.map((c) => {
      if (!c) return "<td></td>";
      if (c.value != null) tot += c.value;
      return `<td>${c.value == null ? "–" : fmt(c.value)}${isEstimate(c) ? "e" : ""}${isGap(c) ? "!" : ""}${c.partial ? "*" : ""}</td>`;
    }).join("");
    return `<tr><th scope="row">${r.year}</th>${tds}<td>${fmt(tot)}</td></tr>`;
  }).join("");
  $("table-wrap").innerHTML = `<table><caption class="sub">${SERIES_LABEL[state.series]} detections per month. – = no data, e = estimate, ! = ${GAP_MIN}+ days without satellite data, * = partial month.</caption>${head}${body}</table>`;
}

// ---------- comparison with the median (step 36) ----------
function median(xs) {
  const a = xs.filter((x) => x != null).sort((p, q) => p - q);
  if (!a.length) return null;
  const k = Math.floor(a.length / 2);
  return a.length % 2 ? a[k] : (a[k - 1] + a[k]) / 2;
}

function fillCompareSelect() {
  const M = state.monthly, sel = $("compare-month");
  const opts = [];
  for (let k = state.range.to; k >= state.range.from; k--)
    opts.push(`<option value="${k}">${monthName(M.months[k])}${M.partial[k] ? " (partial month)" : ""}</option>`);
  sel.innerHTML = opts.join("");
  sel.value = String(state.cmpIdx);
}

// Same calendar month in every other year (full months only).
function compareFull(idx) {
  const M = state.cur, s = state.series, cm = M.months[idx].slice(5);
  const others = [];
  M.months.forEach((ym, k) => {
    if (k !== idx && inRange(k) && ym.slice(5) === cm && !M.partial[k] && M[s][k] != null) others.push({ y: ym.slice(0, 4), v: M[s][k], src: M.src[k] });
  });
  return { value: M[s][idx], others, partial: false };
}

// Partial month: days 1..D of this month vs days 1..D of the same month in other years (mtd block).
function comparePartial() {
  const T = state.cur.mtd, s = state.series, last = T.years.length - 1;
  const pk = state.cur.partial.indexOf(true), mm = state.cur.months[pk].slice(5);
  const yearInRange = (y) => { const k = state.cur.months.indexOf(`${y}-${mm}`); return k >= 0 && inRange(k); };
  const others = T.years.slice(0, last).map((y, k) => ({ y: String(y), v: T[s][k], src: T.src[k] }))
    .filter((o) => o.v != null && yearInRange(o.y));
  return { value: T[s][last], others, partial: true, D: T.through_day,
           lo: T.h_lo ? T.h_lo[last] : null, hi: T.h_hi ? T.h_hi[last] : null };
}

// Percent change against the median of the other years, or why there is none.
function vsMedian(r) {
  const med = median(r.others.map((o) => o.v));
  const few = med != null && med < 5;   // a percentage of a tiny median is misleading
  const pct = !few && med != null && med > 0 && r.value != null ? ((r.value - med) / med) * 100 : null;
  return { med, few, pct };
}

// Collapsed "Details" block inside a card (native details/summary, works with the keyboard).
const detailsHTML = (rows) => (rows.length
  ? `<details class="more"><summary>Details</summary>${rows.map((n) => `<div class="row">${n}</div>`).join("")}</details>` : "");

// Re-render a card but keep its "Details" open (and focused) if the reader had opened it.
function setCard(el, html) {
  const d = el.querySelector("details.more"), open = d && d.open, focused = d && d.contains(document.activeElement);
  el.innerHTML = html;
  const n = el.querySelector("details.more");
  if (n && open) n.open = true;
  if (n && focused) n.querySelector("summary").focus();
}

function cardHTML(title, r, idx) {
  const { med, few, pct } = vsMedian(r);
  const dir = pct == null ? "" : pct >= 0 ? "above" : "below";
  const M = state.cur, rows = [];
  const years = r.others.map((o) => o.y);
  rows.push(`This ${r.partial ? "period" : "month"}: <b>${fmt(r.value)}</b> · median: <b>${fmt(med)}</b> (${years.length} years${years.length ? `, ${years[0]}–${years[years.length - 1]}` : ""})`);
  if (state.series === "h") {
    if (r.partial && r.lo != null) rows.push(`Estimate from NOAA-20 (likely ${fmt(r.lo)}–${fmt(r.hi)}).`);
    else if (idx != null && M.src[idx] !== "V") rows.push(`This month is an estimate (likely ${fmt(M.h_lo[idx])}–${fmt(M.h_hi[idx])}).`);
    if (r.others.some((o) => o.src === "M")) rows.push("The median includes years estimated from MODIS (before 2012).");
  }
  if (idx != null && (M.gap_days || [])[idx] >= GAP_MIN) rows.push(`${M.gap_days[idx]} days without satellite data: value likely too low.`);
  const full = state.range.from === 0 && state.range.to === state.monthly.months.length - 1;
  if (!full) rows.push("The median uses only years inside the selected period.");
  const what = `a typical ${MONTHS_LONG[+M.months[idx].slice(5) - 1]}${r.partial ? ` 1–${r.D}` : ""}`;
  const cls = pct == null ? "" : pct >= 0 ? " up" : " down";
  return `${title ? `<div class="label">${title}</div>` : ""}
    <div class="big${cls}">${few ? "–" : pct == null ? "n/a" : `${pct >= 0 ? "+" : "−"}${Math.abs(pct).toFixed(0)}%`}</div>
    <div class="row one">${few ? "Too few detections for a percentage." : pct == null ? "No other years to compare with." : `${dir} ${what}`}</div>
    ${detailsHTML(rows)}`;
}

// Card 1: the month chosen in the calendar (default: last complete month).
function drawCompare() {
  const M = state.cur, idx = state.cmpIdx;
  if (idx == null || idx < 0) { $("compare").innerHTML = ""; return; }
  const isPartial = M.partial[idx] && M.mtd;
  setCard($("compare"), cardHTML(isPartial ? `So far (days 1–${M.mtd.through_day}) <span class="tag accent">partial</span>` : "",
    isPartial ? comparePartial() : compareFull(idx), idx));
}

// Cards 2-4: partial month, peak month and number of estimated months in the selected period.
function drawSummary() {
  const M = state.cur, s = state.series, { from, to } = state.range;
  const lastShown = to === state.monthly.months.length - 1;
  $("cards-ctx").textContent = `${state.full ? state.meta.name_en : "Selected area"} · ${SERIES_LABEL[s]} · ` +
    `${monthName(M.months[from])} to ${monthName(M.months[to])}${lastShown ? ` · data through ${state.meta.data_through} (UTC)` : ""}`;

  const pk = M.partial.indexOf(true);
  setCard($("card-partial"), M.mtd && pk >= 0 && inRange(pk)
    ? cardHTML(`${monthName(M.months[pk])} so far (days 1–${M.mtd.through_day})`, comparePartial(), pk)
    : `<div class="label">Current month so far</div><div class="big text">–</div><div class="row one">Outside the selected period.</div>`);

  let peak = -1;
  for (let k = from; k <= to; k++) if (M[s][k] != null && (peak < 0 || M[s][k] > M[s][peak])) peak = k;
  const isEst = (k) => s === "h" && state.meta.harmonized && M.src[k] !== "V";
  if (peak < 0) {
    setCard($("card-peak"), `<div class="label">Peak month</div><div class="big text">–</div><div class="row one">No data in the selected period.</div>`);
  } else {
    const rows = [], est = isEst(peak), modis = est && M.src[peak] === "M";
    let measured = "";
    if (est) {
      // Estimated peak: MODIS-based estimates of very active months (Aug–Oct 2009 and 2011) are probably too high.
      const oor = state.monthly.out_of_range && state.monthly.out_of_range[peak];
      rows.push(`Estimated from ${modis ? "MODIS" : "NOAA-20"}, likely ${fmt(M.h_lo[peak])}–${fmt(M.h_hi[peak])}.`);
      if (oor) rows.push("Fire activity was above the level the method was tested on.");
      let mp = -1;
      for (let k = from; k <= to; k++) if (M.src[k] === "V" && M[s][k] != null && (mp < 0 || M[s][k] > M[s][mp])) mp = k;
      if (mp >= 0) measured = `<div class="row one">Measured peak: <button type="button" class="textlink" data-idx="${mp}" aria-label="Measured peak: ${monthName(M.months[mp])}, ${fmt(M[s][mp])} detections. Show in the calendar">${monthName(M.months[mp])}</button> (${fmt(M[s][mp])})</div>`;
    }
    setCard($("card-peak"), `<div class="label">Peak month</div>
       <div class="big text">${monthName(M.months[peak])}</div>
       <div class="row one"><b>${fmt(M[s][peak])}</b>${est ? (modis && state.monthly.out_of_range && state.monthly.out_of_range[peak] ? " · estimate, probably overestimated" : " · estimate") : " detections"}</div>
       ${measured}
       <button type="button" class="linkbtn" data-idx="${peak}" aria-label="Show ${monthName(M.months[peak])} in the calendar">Show in calendar</button>
       ${detailsHTML(rows)}`);
  }

  const n = to - from + 1;
  if (state.meta.harmonized && s === "h") {
    let em = 0, en = 0, oor = 0;
    for (let k = from; k <= to; k++) {
      if (M.src[k] === "M") em++; else if (M.src[k] === "N") en++;
      if (state.monthly.out_of_range && state.monthly.out_of_range[k]) oor++;
    }
    const rows = [];
    if (em) rows.push(`${em} before February 2012 (estimated from MODIS).`);
    if (en) rows.push(`${en} from November 2026 (estimated from NOAA-20).`);
    if (oor) rows.push(`${oor} of them had fire activity above the tested level: probably overestimated.`);
    setCard($("card-est"), `<div class="label">Estimated months</div>
      <div class="big">${em + en}</div>
      <div class="row one">of ${n} months, dashed in the calendar</div>
      ${detailsHTML(rows)}`);
  } else {
    setCard($("card-est"), `<div class="label">Estimated months</div><div class="big">0</div>
      <div class="row one">Raw series: measurements only</div>
      ${detailsHTML([`${n} months in the period.`, "MODIS and VIIRS raw counts are not comparable with each other."])}`);
  }
}

// ---------- charts (monthly lines, yearly totals) ----------
const NS_SVG = "http://www.w3.org/2000/svg";
function svgEl(tag, attrs = {}, parent = null) {
  const e = document.createElementNS(NS_SVG, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (parent) parent.appendChild(e);
  return e;
}
function niceMax(v) {
  if (!(v > 0)) return 10;
  const p = 10 ** Math.floor(Math.log10(v)), f = v / p;
  return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * p;
}
const shortNum = (v) => (v >= 1000 ? `${+(v / 1000).toFixed(1)}k` : `${Math.round(v)}`);
const lineKey = (color, dash, w = 2) =>
  `<svg width="26" height="10" aria-hidden="true"><line x1="1" y1="5" x2="25" y2="5" stroke="${color}" stroke-width="${w}"${dash ? ` stroke-dasharray="${dash}"` : ""}/></svg>`;

function drawCharts() { drawLine(); drawBars(); }

function chartFrame(host, H) {
  const W = Math.max(280, host.clientWidth || 600);
  const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, role: "img" });
  return { svg, W, H, L: 44, R: 10, T: 10, B: 24 };
}
function yAxis(f, ymax) {
  const n = 4;
  for (let i = 0; i <= n; i++) {
    const v = (ymax * i) / n, y = f.T + (f.H - f.T - f.B) * (1 - i / n);
    svgEl("line", { class: "grid", x1: f.L, x2: f.W - f.R, y1: y, y2: y }, f.svg);
    svgEl("text", { x: f.L - 6, y: y + 4, "text-anchor": "end" }, f.svg).textContent = shortNum(v);
  }
}
function placeTipAt(tip, cx, cy) {
  tip.hidden = false;
  const tw = tip.offsetWidth, th = tip.offsetHeight;
  let px = cx + 14, py = cy + 14;
  if (px + tw > window.innerWidth - 8) px = cx - tw - 14;
  if (py + th > window.innerHeight - 8) py = cy - th - 14;
  tip.style.left = Math.max(4, px) + "px"; tip.style.top = Math.max(4, py) + "px";
}

// Monthly line chart: raw MODIS, raw VIIRS and the consistent series with the likely range of the estimates.
function drawLine() {
  const host = $("line-chart");
  if (!host || !state.cur) return;
  const M = state.cur, { from, to } = state.range, n = to - from + 1;
  const harm = state.meta.harmonized, band = harm && M.h_lo;
  const f = chartFrame(host, 240), css = { a: cssVar("--accent"), m: cssVar("--down"), v: cssVar("--viirs") };
  const series = [
    { key: "m", name: "MODIS (raw)", color: css.m, dash: "2 3", w: 1.5 },
    { key: "v", name: "VIIRS (raw)", color: css.v, dash: "6 3", w: 1.5 },
    { key: "h", name: harm ? "Consistent series" : "Combined (raw)", color: css.a, dash: "", w: 2.25 },
  ];
  let ymax = 0;
  for (let k = from; k <= to; k++) for (const s of series) if (M[s.key][k] != null) ymax = Math.max(ymax, M[s.key][k]);
  ymax = niceMax(ymax * 1.05);   // the band may go higher; it is clipped to the plot
  const pw = f.W - f.L - f.R, ph = f.H - f.T - f.B;
  const x = (k) => f.L + (n === 1 ? pw / 2 : ((k - from) / (n - 1)) * pw);
  const y = (v) => f.T + ph * (1 - v / ymax);
  yAxis(f, ymax);
  const y0 = +M.months[from].slice(0, 4), y1 = +M.months[to].slice(0, 4);
  const step = Math.max(1, Math.ceil((y1 - y0 + 1) / Math.max(2, Math.floor(pw / 48))));
  for (let k = from; k <= to; k++) {
    const yy = +M.months[k].slice(0, 4), mm = +M.months[k].slice(5);
    if (mm === 1 && (yy - y0) % step === 0) {
      svgEl("line", { class: "axis", x1: x(k), x2: x(k), y1: f.H - f.B, y2: f.H - f.B + 4 }, f.svg);
      svgEl("text", { x: x(k), y: f.H - 6, "text-anchor": "middle" }, f.svg).textContent = yy;
    }
  }
  svgEl("line", { class: "axis", x1: f.L, x2: f.W - f.R, y1: f.H - f.B, y2: f.H - f.B }, f.svg);
  if (band) {
    let top = "", bot = "";
    for (let k = from; k <= to; k++) {
      if (M.h_lo[k] == null || M.h_hi[k] == null) continue;
      top += `${top ? "L" : "M"}${x(k).toFixed(1)},${y(M.h_hi[k]).toFixed(1)}`;
      bot = `L${x(k).toFixed(1)},${y(M.h_lo[k]).toFixed(1)}` + bot;
    }
    svgEl("defs", {}, f.svg).innerHTML = `<clipPath id="line-clip"><rect x="${f.L}" y="${f.T}" width="${pw}" height="${ph}"/></clipPath>`;
    if (top) svgEl("path", { d: top + bot + "Z", fill: css.a, "fill-opacity": 0.22, stroke: "none", "clip-path": "url(#line-clip)" }, f.svg);
  }
  const shown = [];
  for (const s of series) {
    let d = "", pen = false;
    for (let k = from; k <= to; k++) {
      const v = M[s.key][k];
      if (v == null) { pen = false; continue; }
      d += `${pen ? "L" : "M"}${x(k).toFixed(1)},${y(v).toFixed(1)}`; pen = true;
    }
    if (!d) continue;
    shown.push(s);
    svgEl("path", { d, fill: "none", stroke: s.color, "stroke-width": s.w, "stroke-linejoin": "round", ...(s.dash ? { "stroke-dasharray": s.dash } : {}) }, f.svg);
  }
  if (state.cmpIdx >= from && state.cmpIdx <= to)   // month chosen in the calendar
    svgEl("line", { x1: x(state.cmpIdx), x2: x(state.cmpIdx), y1: f.T, y2: f.H - f.B, stroke: cssVar("--ink"), "stroke-width": 1, "stroke-dasharray": "3 3" }, f.svg);
  const cursor = svgEl("line", { y1: f.T, y2: f.H - f.B, stroke: cssVar("--ink-2"), "stroke-width": 1, visibility: "hidden" }, f.svg);
  let pk = from;
  for (let k = from; k <= to; k++) if ((M.h[k] ?? -1) > (M.h[pk] ?? -1)) pk = k;
  f.svg.setAttribute("aria-label", `Line chart of monthly fire detections, ${monthName(M.months[from])} to ${monthName(M.months[to])}: ` +
    `${shown.map((s) => s.name).join(", ")}. Highest ${series[2].name} month: ${monthName(M.months[pk])}, ${fmt(M.h[pk])}. ` +
    `"Show as table" and "Download CSV" give the exact values.`);
  const tip = $("tooltip");
  f.svg.addEventListener("pointermove", (e) => {
    const r = f.svg.getBoundingClientRect(), sx = ((e.clientX - r.left) / r.width) * f.W;
    const k = Math.min(to, Math.max(from, Math.round(from + ((sx - f.L) / pw) * (n - 1))));
    cursor.setAttribute("x1", x(k)); cursor.setAttribute("x2", x(k)); cursor.setAttribute("visibility", "visible");
    tip.innerHTML = tooltipHTML(k);
    placeTipAt(tip, e.clientX, e.clientY);
  });
  f.svg.addEventListener("pointerleave", () => { tip.hidden = true; cursor.setAttribute("visibility", "hidden"); });
  host.replaceChildren(f.svg);
  $("line-sub").textContent = `${state.full ? state.meta.name_en : "Selected area"}, fire detections per month. ` +
    (harm ? "Compare years with the solid magenta line; the other lines show what each sensor saw." : "Raw counts, not comparable between sensors.");
  $("line-legend").innerHTML = shown.map((s) => `<span class="key">${lineKey(s.color, s.dash, s.w)}${s.name}${s.key === "h" && harm ? " (recommended)" : ""}</span>`).join("") +
    (band ? `<span class="key"><svg width="26" height="10" aria-hidden="true"><rect x="1" y="1" width="24" height="8" rx="2" fill="${css.a}" fill-opacity="0.22"/></svg>Likely range of estimates</span>` : "") +
    `<span class="key">${lineKey(cssVar("--ink"), "3 3", 1)}Month selected in the calendar</span>`;
}

// Yearly totals of the series shown, inside the selected period.
function drawBars() {
  const host = $("bar-chart");
  if (!host || !state.cur) return;
  const M = state.cur, s = state.series, { from, to } = state.range;
  const byYear = new Map();
  for (let k = from; k <= to; k++) {
    const yy = +M.months[k].slice(0, 4);
    if (!byYear.has(yy)) byYear.set(yy, { year: yy, total: 0, months: 0, missing: 0, est: 0, partial: false });
    const o = byYear.get(yy), v = M[s][k];
    o.months++;
    if (v == null) o.missing++; else o.total += v;
    if (M.partial[k]) o.partial = true;
    if (state.meta.harmonized && s === "h" && M.src[k] !== "V") o.est++;
  }
  const years = [...byYear.values()].filter((o) => o.missing < o.months);
  if (!years.length) { host.textContent = "No data for this series in the selected period."; $("bar-legend").innerHTML = ""; return; }
  const f = chartFrame(host, 240), accent = cssVar("--accent");
  const ymax = niceMax(Math.max(...years.map((o) => o.total)));
  yAxis(f, ymax);
  const pw = f.W - f.L - f.R, ph = f.H - f.T - f.B, bw = pw / years.length;
  svgEl("defs", {}, f.svg).innerHTML = `<pattern id="bar-hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <rect width="6" height="6" fill="${accent}" fill-opacity="0.25"/><line x1="0" y1="0" x2="0" y2="6" stroke="${accent}" stroke-width="2"/></pattern>`;
  const lstep = Math.max(1, Math.ceil(years.length / Math.max(2, Math.floor(pw / 40))));
  const kind = (o) => (o.months < 12 || o.partial || o.missing ? "inc" : o.est ? "est" : "meas");
  const tip = $("tooltip");
  years.forEach((o, i) => {
    const gap = Math.min(2, bw * 0.15), x0 = f.L + i * bw + gap, w = Math.max(1, bw - 2 * gap);
    const h = (o.total / ymax) * ph, k = kind(o);
    const bar = svgEl("rect", { x: x0, y: f.T + ph - h, width: w, height: Math.max(0, h), rx: Math.min(3, w / 3),
      fill: k === "inc" ? "url(#bar-hatch)" : accent, "fill-opacity": k === "est" ? 0.55 : 1,
      ...(k === "est" ? { stroke: accent, "stroke-width": 1, "stroke-dasharray": "3 2" } : {}) }, f.svg);
    bar.addEventListener("pointermove", (e) => {
      const notes = [];
      if (o.est) notes.push(`${o.est} estimated month${o.est > 1 ? "s" : ""}`);
      if (o.months < 12) notes.push(`only ${o.months} month${o.months > 1 ? "s" : ""} in the period`);
      if (o.partial) notes.push("includes the current, unfinished month");
      if (o.missing) notes.push(`${o.missing} month${o.missing > 1 ? "s" : ""} without data`);
      tip.innerHTML = `<div><b>${o.year}</b></div><div>${SERIES_LABEL[s]}: <b>${fmt(o.total)}</b></div>${notes.map((t) => `<div class="t-muted">${t}</div>`).join("")}`;
      placeTipAt(tip, e.clientX, e.clientY);
    });
    bar.addEventListener("pointerleave", () => { tip.hidden = true; });
    if (i % lstep === 0)
      svgEl("text", { x: x0 + w / 2, y: f.H - 6, "text-anchor": "middle" }, f.svg).textContent = lstep > 1 || bw < 34 ? `'${String(o.year).slice(2)}` : o.year;
  });
  svgEl("line", { class: "axis", x1: f.L, x2: f.W - f.R, y1: f.H - f.B, y2: f.H - f.B }, f.svg);
  const full = years.filter((o) => kind(o) !== "inc"), top = (full.length ? full : years).reduce((a, b) => (b.total > a.total ? b : a));
  f.svg.setAttribute("aria-label", `Bar chart of yearly totals, ${SERIES_LABEL[s]}, ${years[0].year} to ${years[years.length - 1].year}. ` +
    `Highest ${full.length ? "complete " : ""}year: ${top.year}, ${fmt(top.total)} detections.`);
  host.replaceChildren(f.svg);
  $("bar-sub").textContent = `${SERIES_LABEL[s]}, sum of the months in the selected period.`;
  const sw = (fill, extra = "") => `<svg width="14" height="14" aria-hidden="true"><rect x="0.5" y="0.5" width="13" height="13" rx="3" fill="${fill}" ${extra}/></svg>`;
  const anyEst = years.some((o) => kind(o) === "est"), anyInc = years.some((o) => kind(o) === "inc");
  $("bar-legend").innerHTML = `<span class="key">${sw(accent)}${anyEst ? "Measured year" : "Year total"}</span>` +
    (anyEst ? `<span class="key">${sw(accent, `fill-opacity="0.55" stroke="${accent}" stroke-dasharray="3 2"`)}Includes estimates</span>` : "") +
    (anyInc ? `<span class="key">${sw("url(#bar-hatch)", `stroke="${accent}"`)}Incomplete year (not comparable)</span>` : "");
}

// ---------- CSV download (step 37) ----------
const csvCell = (v, force = false) => (v == null ? "" : force || /[",\r\n]/.test(String(v)) ?`"${String(v).replace(/"/g, '""')}"` : String(v));
const trimNum = (x) => String(+(+x).toFixed(2));

// Latitude/longitude range for the file name, e.g. "36-38.6N" and "27-32.5E".
function degRange(a, b, pos, neg) {
  const tag = (x) => (x >= 0 ? pos : neg);
  const A = Math.abs(a), B = Math.abs(b);
  return tag(a) === tag(b) ? `${trimNum(A)}-${trimNum(B)}${tag(a)}` : `${trimNum(A)}${tag(a)}-${trimNum(B)}${tag(b)}`;
}

function csvFileName() {
  const months = state.monthly.months, a = months[state.range.from], b = months[state.range.to];
  const where = state.full ? state.region
    : `${degRange(state.bbox.south, state.bbox.north, "N", "S")}_${degRange(state.bbox.west, state.bbox.east, "E", "W")}`;
  return `burn-calendar_${where}_${a}_${b}.csv`;
}

function buildCsv(today = new Date().toISOString().slice(0, 10)) {
  const M = state.cur, meta = state.meta, harm = meta.harmonized, k20 = meta.viirs_switch ? meta.viirs_switch.k_n20 : "k";
  const months = M.months;
  const area = state.full ? `${meta.name_en} (whole region)`
    : `selected rectangle ${fmtDeg(state.bbox.south)}-${fmtDeg(state.bbox.north)} N, ${fmtDeg(state.bbox.west)}-${fmtDeg(state.bbox.east)} E (${state.cur.nCells} grid cells of ${state.grid.cell_deg} degrees)`;
  const comments = [
    meta.acknowledgment,
    harm ? "Harmonized values before 2012 are estimates: MODIS counts converted to VIIRS S-NPP equivalent with a monthly factor. From November 2026 values are estimated from VIIRS NOAA-20."
         : "Raw combined series (MODIS before 2012, VIIRS after); not harmonized.",
    `Unit: ${meta.unit}, per calendar month (UTC). Data through ${meta.data_through}. Generated ${today}.`,
    `Area: ${area}. Period: ${months[state.range.from]} to ${months[state.range.to]}.`,
    "Columns: likely_low and likely_high give the likely range for estimated months; days_without_data counts days with no satellite data (3 or more days: value likely too low); partial_month = 1 means the month is not finished (value covers days 1 to " + (M.mtd ? M.mtd.through_day : "?") + ").",
  ];
  if (!state.full) comments.push("Small areas: estimates before 2012 are rough.");
  if (meta.quality === "experimental")
    comments.splice(1, 0, "Experimental: " + (meta.quality_note || EXP_DEFAULT));
  if (meta.box_region && meta.overlaps_turkiye !== false)
    comments.push("Boxes overlap Türkiye; for Turkish territory use the Türkiye view (pre-2012 estimates can differ between views).");
  const lines = ["sep=,", ...comments.map((c) => csvCell(`# ${c}`, true)),
    "year,month,harmonized_count,source,estimate_flag,likely_low,likely_high,days_without_data,partial_month"];
  for (let k = state.range.from; k <= state.range.to; k++) {
    const [y, m] = months[k].split("-"), src = M.src[k], est = harm && src !== "V";
    const source = !harm ? "raw combined (not harmonized)"
      : src === "V" ? "measured (VIIRS S-NPP)"
      : src === "M" ? "estimated (MODIS x monthly factor)" : `estimated (VIIRS NOAA-20 x ${k20})`;
    const rnd = (x) => (x == null ? "" : Math.round(x));
    lines.push([+y, +m, rnd(M.h[k]), source, est ? 1 : 0,
      est && M.h_lo ? rnd(M.h_lo[k]) : "", est && M.h_hi ? rnd(M.h_hi[k]) : "",
      (M.gap_days || [])[k] || 0, M.partial[k] ? 1 : 0].map((v) => csvCell(v)).join(","));
  }
  return lines.join("\r\n") + "\r\n";
}

function downloadCsv() {
  const text = buildCsv(), name = csvFileName();
  // UTF-8 byte order mark so Excel reads the text correctly.
  const blob = new Blob(["﻿", text], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob), a = document.createElement("a");
  a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
  $("csv-status").textContent = `Downloaded ${name} (${state.range.to - state.range.from + 1} months).`;
}

// ---------- wiring ----------
async function init() {
  try {
    const idx = await getJSON("data/index.json");
    const sel = $("region");
    sel.innerHTML = idx.regions.map((r) =>
      `<option value="${r.id}">${r.name_en}${r.quality === "experimental" ? " (experimental)" : ""}</option>`).join("");
    idx.regions.forEach((r) => { regionNames[r.id] = r.name_en; });
    sel.addEventListener("change", async () => {
      const want = sel.value;
      try { await loadRegion(want); } catch (err) {
        showLoadError(err, regionNames[want] || want);
        document.querySelector("main").removeAttribute("aria-busy");
        if (state.region) { sel.value = state.region; render(); }
      }
    });
    $("series").addEventListener("change", (e) => { state.series = e.target.value; state._userPicked = true; render(); });
    $("toggle-table").addEventListener("click", (e) => {
      state.table = !state.table;
      e.target.setAttribute("aria-pressed", String(state.table));
      e.target.textContent = state.table ? "Hide table" : "Show as table";
      $("table-wrap").hidden = !state.table;
      if (state.table) drawTable();
    });
    $("bbox-form").addEventListener("submit", (e) => {
      e.preventDefault();
      const v = (k) => parseFloat($(`b-${k}`).value);
      const b = { north: v("north"), south: v("south"), west: v("west"), east: v("east") };
      if (Object.values(b).some(Number.isNaN)) { $("bbox-status").textContent = "Enter all four coordinates."; return; }
      setBbox(b);
    });
    $("reset-btn").addEventListener("click", () => setBbox(regionBbox(), true));
    $("compare-month").addEventListener("change", (e) => { state.focusIdx = null; selectMonth(+e.target.value); });
    for (const p of ["from", "to"])
      for (const part of ["year", "month"]) $(`${p}-${part}`).addEventListener("change", () => onPeriodChange(p));
    $("period-reset").addEventListener("click", resetPeriod);
    $("csv-btn").addEventListener("click", downloadCsv);
    heatWire();
    shareWire();
    let t;
    window.addEventListener("resize", () => { clearTimeout(t); t = setTimeout(() => { drawCalendar(); drawCharts(); }, 150); });
    $("card-peak").addEventListener("click", (e) => {
      const b = e.target.closest("button[data-idx]");
      if (!b) return;
      const k = +b.dataset.idx;
      state.focusIdx = k;
      selectMonth(k);
      const cell = document.querySelector(`#calendar rect.cell[data-idx="${k}"]`);
      if (cell) { document.querySelectorAll("#calendar rect.cell").forEach((r) => r.setAttribute("tabindex", r === cell ? "0" : "-1")); cell.focus(); }
    });
    const ids = idx.regions.map((r) => r.id), p = shareRead(ids);
    const first = p.region || ids[0];
    sel.value = first;
    await loadRegion(first);
    try { shareApply(p); } catch (e) { await loadRegion(first); }   // a bad link falls back to the default view
    share.ready = true;
    shareWrite();
  } catch (err) {
    showLoadError(err, "this page");
    document.querySelector("main").removeAttribute("aria-busy");
    $("calendar").textContent = "";
    $("cards-ctx").textContent = "";
  }
}
init();
