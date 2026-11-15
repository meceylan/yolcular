// AI-assisted: generated with Claude (Anthropic)
// Step 75: shareable view link. The address keeps only view settings (region id, area box, period,
// selected month, series, map mode); nothing personal. Invalid or missing values fall back to the default view.
// Loaded before app.js; uses app.js globals at call time.
"use strict";

const share = { ready: false, timer: null };
const YM_RE = /^\d{4}-(0[1-9]|1[0-2])$/;

function shareRead(regionIds) {
  const q = new URLSearchParams(location.search), p = {};
  const region = q.get("region");
  if (region && regionIds.includes(region)) p.region = region;
  for (const k of ["ym", "from", "to"]) { const v = q.get(k); if (v && YM_RE.test(v)) p[k] = v; }
  const box = (q.get("box") || "").split(",").map(Number);
  if (box.length === 4 && box.every(Number.isFinite)) {
    const [south, west, north, east] = box;
    if (Math.abs(south) <= 90 && Math.abs(north) <= 90 && Math.abs(west) <= 180 && Math.abs(east) <= 180 && south < north && west < east)
      p.box = { south, west, north, east };
  }
  const s = q.get("series");
  if (["h", "m", "v"].includes(s)) p.series = s;
  if (q.get("map") === "period") p.map = "period";
  return p;
}

// Restore a view after the region has loaded. Anything that does not fit the data is ignored.
function shareApply(p) {
  const M = state.monthly.months, ix = (ym) => (ym ? M.indexOf(ym) : -1);
  let from = ix(p.from), to = ix(p.to);
  if (from >= 0 || to >= 0) {
    if (from < 0) from = 0;
    if (to < 0) to = M.length - 1;
    if (from <= to) { state.range = { from, to }; syncPeriodSelects(); }
  }
  const k = ix(p.ym);
  if (k >= state.range.from && k <= state.range.to && k >= 0) state.cmpIdx = k; else ensureCompareMonth();
  fillCompareSelect();
  state.focusIdx = null;
  state.mapMode = p.map === "period" ? "period" : "month";
  if (p.series && (state.meta.harmonized || p.series !== "h")) {
    state.series = p.series; state._userPicked = true; $("series").value = p.series;
  }
  const before = state.cur;
  if (p.box) setBbox(p.box);
  if (state.cur === before) render();
}

function shareURL() {
  if (!state.monthly) return location.href;
  const M = state.monthly.months, q = new URLSearchParams();
  q.set("region", state.region);
  if (!state.full && state.bbox) {
    const b = state.bbox, f = (x) => String(+(+x).toFixed(2));
    q.set("box", [b.south, b.west, b.north, b.east].map(f).join(","));
  }
  if (state.range.from !== 0 || state.range.to !== M.length - 1) { q.set("from", M[state.range.from]); q.set("to", M[state.range.to]); }
  if (state.cmpIdx != null && state.cmpIdx >= 0) q.set("ym", M[state.cmpIdx]);
  if (state.series !== (state.meta.harmonized ? "h" : "m")) q.set("series", state.series);
  if (state.mapMode === "period") q.set("map", "period");
  return `${location.origin}${location.pathname}?${q.toString().replace(/%2C/g, ",")}`;
}

// Keep the address in step with the view, without reloading or adding history entries.
function shareWrite() {
  if (!share.ready) return;
  const url = shareURL();
  if (url !== location.href) {
    try { history.replaceState(null, "", url); } catch (e) { /* some sandboxed frames refuse; the button still works */ }
  }
}

async function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    try { await navigator.clipboard.writeText(text); return true; } catch (e) { /* fall through */ }
  }
  const ta = document.createElement("textarea");
  ta.value = text; ta.setAttribute("readonly", ""); ta.style.position = "fixed"; ta.style.opacity = "0";
  document.body.appendChild(ta); ta.select();
  let ok = false;
  try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
  ta.remove();
  return ok;
}

function shareWire() {
  const btn = $("copy-link"), status = $("copy-status");
  btn.addEventListener("click", async () => {
    const url = shareURL();
    const ok = await copyText(url);
    clearTimeout(share.timer);
    btn.textContent = ok ? "Copied" : "Copy link";
    status.textContent = ok ? "Link copied to the clipboard." : `Copy failed. Link: ${url}`;
    share.timer = setTimeout(() => { btn.textContent = "Copy link"; if (ok) status.textContent = ""; }, 2500);
  });
}
