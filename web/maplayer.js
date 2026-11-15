// AI-assisted: generated with Claude (Anthropic)
// Step 74: fire density layer on the map. Reads the region's 0.25° grid (data/<region>/grid.json, already
// loaded by app.js) and paints each cell with the same inferno ramp as the calendar (log scale).
// The layer is one canvas in its own pane with pointer-events off, so map dragging and rectangle
// drawing keep working. Only cells inside the visible map area are drawn.
// Loaded before app.js; uses app.js globals (state, $, colorAt, fmt, monthName, selectMonth, ...) at call time.
"use strict";

const HEAT_ALPHA = 0.78;
const HEAT_COL = { h: 1, m: 2, v: 3 };          // position in grid.json cell.d rows: [k, h, m, v]
const PLAY_MS = { slow: 1600, normal: 850, fast: 400 };
const heat = {
  map: null, canvas: null, on: true, key: null,
  cells: null, byMonth: null, cellAt: null,      // per region + series index
  cache: new Map(),                              // values and scales per mode/period
  view: null,                                    // what is drawn now: { list, vals, sc, ... }
  hl: null, playing: false, timer: null, drawEndAt: 0,
};
const reducedMotion = () => !!(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches);

// ---------- index (once per region and series) ----------
function heatIndex() {
  const key = `${state.region}|${state.series}`;
  if (heat.key === key) return;
  const g = state.grid, n = state.monthly.months.length, col = HEAT_COL[state.series];
  const byMonth = Array.from({ length: n }, () => []), cellAt = new Map();
  g.cells.forEach((c, ci) => {
    cellAt.set(c.i * 10000 + c.j, ci);
    for (const r of c.d) if (r[col] != null && r[col] > 0) byMonth[r[0]].push([ci, r[col]]);
  });
  Object.assign(heat, { key, cells: g.cells, byMonth, cellAt });
  heat.cache.clear();
}

// Log colour scale over the given positive values (same rule as scaleFor() in app.js).
function heatScale(min, max) {
  if (!(max > 0)) { min = 1; max = 10; }
  const lo = Math.log10(min), hi = Math.max(Math.log10(max), lo + 1);
  return { min, max, lo, hi, t: (v) => (Math.log10(Math.max(v, min)) - lo) / (hi - lo) };
}

// Values shown now: one month (mode "month") or the sum over the period (mode "period").
function heatValues() {
  heatIndex();
  const { from, to } = state.range, mode = state.mapMode || "month", k = state.cmpIdx;
  const ck = mode === "month" ? `m|${from}|${to}|${k}` : `p|${from}|${to}`;
  if (heat.cache.has(ck)) return heat.cache.get(ck);
  let list;
  if (mode === "month") {
    list = heat.byMonth[k] || [];
  } else {
    const sum = new Map();
    for (let m = from; m <= to; m++) for (const [ci, v] of heat.byMonth[m]) sum.set(ci, (sum.get(ci) || 0) + v);
    list = [...sum.entries()];
  }
  // Month mode: one fixed scale for every month of the period, so playback compares like with like.
  let min = Infinity, max = 0;
  const scan = (arr) => { for (const [, v] of arr) { if (v < min) min = v; if (v > max) max = v; } };
  if (mode === "month") for (let m = from; m <= to; m++) scan(heat.byMonth[m]); else scan(list);
  const sc = heatScale(min === Infinity ? 1 : Math.max(min, 0.1), max);
  const vals = new Map(list);
  const out = { list, vals, sc, mode, k, from, to };
  if (heat.cache.size > 60) heat.cache.clear();
  heat.cache.set(ck, out);
  return out;
}

// ---------- canvas ----------
const LUT = [];
function lutColor(t) {
  const q = Math.round(Math.min(1, Math.max(0, t)) * 255);
  return LUT[q] || (LUT[q] = colorAt(q / 255));
}

function heatInit(map) {
  heat.map = map;
  const pane = map.createPane("heat");
  pane.style.zIndex = 350; pane.style.pointerEvents = "none";
  heat.canvas = L.DomUtil.create("canvas", "heat-canvas", pane);
  heat.canvas.setAttribute("aria-hidden", "true");
  map.on("moveend zoomend resize viewreset", heatDraw);
  map.on("zoomstart", () => { heat.canvas.style.visibility = "hidden"; });
  map.on("mousemove", heatHover);
  map.on("mouseout", heatHideTip);
  map.on("click", heatTap);
  // Corner label: month or period shown, and "estimated" when the values are estimates.
  const Badge = L.Control.extend({ onAdd() { const d = L.DomUtil.create("div", "heat-badge"); d.setAttribute("aria-hidden", "true"); return d; } });
  heat.badge = new Badge({ position: "topright" }).addTo(map).getContainer();
  const el = map.getContainer();
  // Remember when a rectangle drawing ends so the click that follows is not taken as a tap on a cell.
  el.addEventListener("pointerup", () => { if (el.classList.contains("drawing")) heat.drawEndAt = Date.now(); }, true);
  // Keyboard: arrow keys pan the map (Leaflet); the cell under the centre cross is read out.
  el.addEventListener("focus", () => { el.classList.add("kbd"); heatReadCentre(); });
  el.addEventListener("blur", () => { el.classList.remove("kbd"); });
  map.on("moveend", () => { if (document.activeElement === el) heatReadCentre(); });
}

function heatDraw() {
  const map = heat.map, c = heat.canvas;
  if (!map || !c || !state.grid || !map._loaded) return;   // the map gets its first view after layout
  const size = map.getSize(), dpr = Math.min(2, window.devicePixelRatio || 1);
  if (c.width !== Math.round(size.x * dpr) || c.height !== Math.round(size.y * dpr)) {
    c.width = Math.round(size.x * dpr); c.height = Math.round(size.y * dpr);
    c.style.width = size.x + "px"; c.style.height = size.y + "px";
  }
  L.DomUtil.setPosition(c, map.containerPointToLayerPoint([0, 0]));
  c.style.visibility = "";
  const ctx = c.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, size.x, size.y);
  if (!heat.on || !heat.view) return;
  const cell = state.grid.cell_deg, b = map.getBounds();
  const iLo = Math.floor((b.getSouth() + 90) / cell) - 1, iHi = Math.ceil((b.getNorth() + 90) / cell);
  const jLo = Math.floor((b.getWest() + 180) / cell) - 1, jHi = Math.ceil((b.getEast() + 180) / cell);
  const { list, sc } = heat.view;
  ctx.globalAlpha = HEAT_ALPHA;
  for (const [ci, v] of list) {
    const g = heat.cells[ci];
    if (g.i < iLo || g.i > iHi || g.j < jLo || g.j > jHi) continue;   // outside the visible area
    const la = g.i * cell - 90, lo = g.j * cell - 180;
    const p = map.latLngToContainerPoint([la + cell, lo]), q = map.latLngToContainerPoint([la, lo + cell]);
    ctx.fillStyle = lutColor(sc.t(v));
    ctx.fillRect(p.x, p.y, Math.max(1, q.x - p.x), Math.max(1, q.y - p.y));
  }
  ctx.globalAlpha = 1;
  if (heat.hl) {   // highlighted cell: dark outer and light inner outline, visible on any fill
    const la = heat.hl.i * cell - 90, lo = heat.hl.j * cell - 180;
    const p = map.latLngToContainerPoint([la + cell, lo]), q = map.latLngToContainerPoint([la, lo + cell]);
    const w = q.x - p.x, h = q.y - p.y;
    ctx.lineWidth = 3; ctx.strokeStyle = "#0d0f13"; ctx.strokeRect(p.x - 1, p.y - 1, w + 2, h + 2);
    ctx.lineWidth = 1.5; ctx.strokeStyle = "#ffffff"; ctx.strokeRect(p.x + 0.75, p.y + 0.75, Math.max(1, w - 1.5), Math.max(1, h - 1.5));
  }
}

// ---------- text ----------
const hemi = (v, pos, neg) => `${nf(Math.abs(v), 2)}° ${t(`dir.${v >= 0 ? pos : neg}`)}`;
function cellPlace(i, j) {
  const cell = state.grid.cell_deg, la = i * cell - 90, lo = j * cell - 180;
  return t("map.cellrange", { a: hemi(la, "N", "S"), b: hemi(la + cell, "N", "S"), c: hemi(lo, "E", "W"), d: hemi(lo + cell, "E", "W") });
}
function cellCentreText(i, j) {
  const cell = state.grid.cell_deg;
  return `${hemi((i + 0.5) * cell - 90, "N", "S")}, ${hemi((j + 0.5) * cell - 180, "E", "W")}`;
}
const fmtCell = (v) => (v > 0 && v < 10 && v % 1 ? nf(v, 1) : fmt(v));

function heatWhen() {
  const V = heat.view, M = state.monthly;
  if (!V) return "";
  if (V.mode === "month") return monthName(M.months[V.k]);
  return t("map.periodtotal", { a: monthName(M.months[V.from]), b: monthName(M.months[V.to]) });
}

// Notes about the values shown: estimated months, partial month, missing data.
function heatNotes() {
  const V = heat.view, M = state.monthly, harm = state.meta.harmonized && state.series === "h";
  const notes = [];
  let est = false;
  if (V.mode === "month") {
    const src = M.src[V.k];
    if (harm && src === "M") { est = true; notes.push(t("map.estM")); }
    else if (harm && src === "N") { est = true; notes.push(t("map.estN", { k: nf(state.meta.viirs_switch.k_n20, 3) })); }
    if (M.partial[V.k]) notes.push(t("map.partial", { d: M.mtd ? M.mtd.through_day : "?" }));
    if (M[state.series][V.k] == null) notes.push(t("map.nodata"));
    if ((M.gap_days || [])[V.k] >= GAP_MIN) notes.push(t("map.gap", { g: M.gap_days[V.k] }));
  } else {
    let n = 0;
    for (let k = V.from; k <= V.to; k++) if (harm && M.src[k] !== "V") n++;
    if (n) { est = true; notes.push(t("map.includes", { n })); }
  }
  return { est, notes };
}

function heatTipHTML(i, j) {
  const ci = heat.cellAt.get(i * 10000 + j);
  const v = ci == null ? 0 : heat.view.vals.get(ci) || 0;
  const { est } = heatNotes();
  return `<div>${t("map.tipcount", { v: fmtCell(v), one: v === 1, est })}</div>` +
    `<div class="t-muted">${heatWhen()}</div><div class="t-muted">${t("map.cell", { p: cellPlace(i, j) })}</div>`;
}
const tipText = (i, j) => { const d = document.createElement("div"); d.innerHTML = heatTipHTML(i, j); return [...d.children].map((x) => x.textContent).join(". ") + "."; };

// Grid cell under a map position, or null outside the region box.
function cellAtLatLng(ll) {
  const R = state.meta.bbox, cell = state.grid.cell_deg;
  if (ll.lat < R.south || ll.lat > R.north || ll.lng < R.west || ll.lng > R.east) return null;
  return { i: Math.floor((ll.lat + 90) / cell), j: Math.floor((ll.lng + 180) / cell) };
}

function heatHover(e) {
  if (!heat.on || !heat.view || heat.map.getContainer().classList.contains("drawing")) { heatHideTip(); return; }
  const c = cellAtLatLng(e.latlng), tip = $("tooltip");
  if (!c) { heatHideTip(); return; }
  if (!heat.hl || heat.hl.i !== c.i || heat.hl.j !== c.j) { heat.hl = c; heatDraw(); }
  tip.innerHTML = heatTipHTML(c.i, c.j);
  placeTipAt(tip, e.originalEvent.clientX, e.originalEvent.clientY);
}
function heatHideTip() {
  $("tooltip").hidden = true;
  if (heat.hl && !heat.pinned) { heat.hl = null; heatDraw(); }
}
// Tap or click (touch screens have no hover): pin the cell and read it out below the map.
function heatTap(e) {
  if (!heat.on || !heat.view || Date.now() - heat.drawEndAt < 400 || heat.map.getContainer().classList.contains("drawing")) return;
  const c = cellAtLatLng(e.latlng);
  if (!c) return;
  heat.hl = c; heat.pinned = true; heatDraw();
  $("heat-readout").textContent = tipText(c.i, c.j);
}
function heatReadCentre() {
  if (!heat.on || !heat.view || !heat.map._loaded) return;
  const c = cellAtLatLng(heat.map.getCenter());
  $("heat-readout").textContent = c ? t("map.centre", { t: tipText(c.i, c.j) }) : t("map.outside");
  heat.hl = c; heat.pinned = !!c; heatDraw();
}

// ---------- panel: caption, legend, top 5 ----------
function heatPanel() {
  const V = heat.view, { est, notes } = heatNotes(), sc = V.sc;
  const label = state.series === "h" ? "" : ` (${SERIES_LABEL[state.series]})`;
  heat.badge.innerHTML = `<b>${heatWhen()}</b>${est ? `<span class="est">${t("map.estbadge")}</span>` : ""}`;
  heat.badge.hidden = !heat.on;

  // Top 5 cells inside the selected area (whole region by default).
  const b = state.bbox, cell = state.grid.cell_deg;
  const inSel = V.list.filter(([ci]) => {
    const g = heat.cells[ci], la = (g.i + 0.5) * cell - 90, lo = (g.j + 0.5) * cell - 180;
    return la >= b.south && la <= b.north && lo >= b.west && lo <= b.east;
  });
  const top = [...inSel].sort((a, c) => c[1] - a[1]).slice(0, 5);
  const where = state.full ? regionName(state.region) : t("map.selarea");
  $("heat-top-title").textContent = t("map.toptitle", { where });
  $("heat-top").innerHTML = top.length
    ? top.map(([ci, v], r) => {
        const g = heat.cells[ci];
        return `<li><button type="button" class="textlink" data-i="${g.i}" data-j="${g.j}" aria-label="${t("map.toparia", { r: r + 1, p: cellCentreText(g.i, g.j), v: fmtCell(v) })}">${cellCentreText(g.i, g.j)}</button> <b>${fmtCell(v)}</b></li>`;
      }).join("")
    : `<li class="none">${t("map.nodet", { where })}</li>`;

  const total = inSel.reduce((s, [, v]) => s + v, 0);
  const desc = t("map.desc", { cell: nf(cell, 2), label, when: heatWhen() }) +
    (top.length ? t("map.descn", { n: nf(inSel.length), where, total: fmtCell(total), p: cellCentreText(heat.cells[top[0][0]].i, heat.cells[top[0][0]].j), v: fmtCell(top[0][1]) })
                : `${t("map.nodet", { where })} `) + notes.join(" ");
  const d = $("heat-desc");
  d.setAttribute("aria-live", heat.playing ? "off" : "polite");
  d.textContent = desc;

  // Legend: same inferno ramp as the calendar, its own range (detections per cell).
  const stops = Array.from({ length: 11 }, (_, i) => `${colorAt(i / 10)} ${i * 10}%`).join(",");
  const short = (v) => (v < 10 && v % 1 ? nf(v, 1) : shortNum(v));
  const mid = 10 ** ((sc.lo + sc.hi) / 2);
  $("heat-legend").innerHTML = `<span class="hl-title">${V.mode === "month" ? t("map.legmonth") : t("map.legperiod")} <span class="t-muted">${t("map.leglog")}</span></span>
    <div class="bar" style="background:linear-gradient(90deg,${stops});opacity:${HEAT_ALPHA}"></div>
    <div class="hl-ticks"><span>${short(sc.min)}</span><span>${short(mid)}</span><span>${short(sc.max)}</span></div>
    <span class="t-muted">${t("map.legzero")}${est ? t("map.legest") : ""}</span>`;
  $("heat-legend").setAttribute("aria-label", t("map.legaria", { min: short(sc.min), max: short(sc.max) }));
  $("heat-mode").value = V.mode;
}

// Called by app.js after every render and month change.
function heatUpdate() {
  if (!heat.map || !state.grid || state.cmpIdx == null) return;
  heat.view = heatValues();
  if (!heat.pinned) heat.hl = null;
  heatDraw();
  heatPanel();
  $("heat-play").disabled = state.range.from === state.range.to;
}

// ---------- playback ----------
function heatSetPlaying(on) {
  heat.playing = on;
  clearTimeout(heat.timer);
  const btn = $("heat-play");
  btn.setAttribute("aria-pressed", String(on));
  btn.textContent = on ? t("pause") : t("play");
  btn.setAttribute("aria-label", on ? t("pause.aria") : t("play.aria"));
  $("heat-desc").setAttribute("aria-live", on ? "off" : "polite");
  if (!on) { if (heat.view) heatPanel(); return; }
  if (state.mapMode !== "month" || state.cmpIdx >= state.range.to || state.cmpIdx < state.range.from) {
    state.mapMode = "month";
    heatStepTo(state.cmpIdx >= state.range.to || state.cmpIdx < state.range.from ? state.range.from : state.cmpIdx);
  }
  heatTick();
}
function heatTick() {
  if (!heat.playing) return;
  heat.timer = setTimeout(() => {
    if (!heat.playing) return;
    if (state.cmpIdx >= state.range.to) { heatSetPlaying(false); return; }
    heatStepTo(state.cmpIdx + 1);
    heatTick();
  }, PLAY_MS[$("heat-speed").value] || PLAY_MS.normal);
}
function heatStepTo(k) {
  k = Math.min(state.range.to, Math.max(state.range.from, k));
  state.focusIdx = k;
  selectMonth(k);   // also redraws the calendar ring, the comparison card and the map
}

function heatWire() {
  $("heat-on").addEventListener("change", (e) => {
    heat.on = e.target.checked;
    if (!heat.on) { heatHideTip(); heat.pinned = false; heat.hl = null; }
    heatDraw();
    heat.badge.hidden = !heat.on;
  });
  $("heat-mode").addEventListener("change", (e) => {
    if (heat.playing) heatSetPlaying(false);
    state.mapMode = e.target.value; heatUpdate();
  });
  $("heat-play").addEventListener("click", () => heatSetPlaying(!heat.playing));
  $("heat-prev").addEventListener("click", () => { heatSetPlaying(false); state.mapMode = "month"; heatStepTo(state.cmpIdx - 1); });
  $("heat-next").addEventListener("click", () => { heatSetPlaying(false); state.mapMode = "month"; heatStepTo(state.cmpIdx + 1); });
  if (reducedMotion()) {
    $("heat-speed").value = "slow";
    $("heat-motion").hidden = false;
  }
  const show = (e, pan) => {
    const b = e.target.closest("button[data-i]");
    if (!b || !heat.map) return;
    const c = { i: +b.dataset.i, j: +b.dataset.j }, cell = state.grid.cell_deg;
    heat.hl = c; heat.pinned = true; heatDraw();
    $("heat-readout").textContent = tipText(c.i, c.j);
    if (pan && heat.map._loaded) {
      const ll = L.latLng((c.i + 0.5) * cell - 90, (c.j + 0.5) * cell - 180);
      if (!heat.map.getBounds().contains(ll)) heat.map.panTo(ll, { animate: !reducedMotion() });
    }
  };
  $("heat-top").addEventListener("click", (e) => show(e, true));
  $("heat-top").addEventListener("focusin", (e) => show(e, false));
}

// Esc dismisses the hover/focus tooltip (WCAG 1.4.13) and pauses playback (WCAG 2.2.2).
document.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  const tip = $("tooltip");
  if (tip && !tip.hidden) tip.hidden = true;
  if (heat.playing) heatSetPlaying(false);
});
