// AI-assisted: generated with Claude (Anthropic)
// Step 77: "Climate context" box. Monthly temperature and precipitation from NASA POWER (precomputed in
// data/<region>/climate.json by scripts/fetch_power.py; the page makes no API call), as a fire-weighted average of
// 5 points in the region's most fire-active areas, shown as the difference from the 2002–2025 average of the same calendar month.
// Shown alongside the fire counts; no causal claim. Loaded before app.js; uses its globals at call time.
"use strict";

async function loadClimate(id) {
  try { state.climate = await getJSON(`data/${id}/climate.json`); } catch (e) { state.climate = null; }
}

function climateStats(C, ym) {
  const k = C.months.indexOf(ym);
  const mm = ym.slice(5), [b0, b1] = (C.baseline || "2002-2025").split("-").map(Number);
  const avg = (key) => {
    const xs = C.months.map((m, i) => (m.slice(5) === mm && +m.slice(0, 4) >= b0 && +m.slice(0, 4) <= b1 ? C[key][i] : null)).filter((v) => v != null);
    return xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null;
  };
  return { k, t: k >= 0 ? C.t2m[k] : null, p: k >= 0 ? C.prec[k] : null, tAvg: avg("t2m"), pAvg: avg("prec"), b0, b1 };
}

function drawClimate() {
  const box = $("climate");
  if (!box) return;
  const C = state.climate;
  if (!C || !state.monthly || state.cmpIdx == null || state.cmpIdx < 0) { box.hidden = true; return; }
  box.hidden = false;
  const ym = state.monthly.months[state.cmpIdx], name = monthName(ym), cal = MONTHS_LONG[+ym.slice(5) - 1];
  const s = climateStats(C, ym);
  const sign = (d, dec) => `${d >= 0 ? "+" : "−"}${Math.abs(d).toFixed(dec)}`;
  const rows = [];
  if (s.t != null && s.tAvg != null) {
    const d = s.t - s.tAvg;
    rows.push(`<div class="cl-row"><span class="cl-k">Temperature</span> <b>${sign(d, 1)} °C</b> <span class="t-muted">vs. average (${s.t.toFixed(1)} °C; average ${s.tAvg.toFixed(1)} °C)</span></div>`);
  }
  if (s.p != null && s.pAvg != null) {
    const d = s.p - s.pAvg;
    rows.push(`<div class="cl-row"><span class="cl-k">Precipitation</span> <b>${sign(d, 0)} mm</b> <span class="t-muted">vs. average (${Math.round(s.p)} mm; average ${Math.round(s.pAvg)} mm)</span></div>`);
  }
  if (!rows.length) rows.push(`<div class="cl-row t-muted">No climate data for ${name} yet (available to ${monthName(C.months[C.months.length - 1])}).</div>`);
  const local = state.full ? "" : " Not specific to the drawn area.";
  box.innerHTML = `<h3 id="climate-title" class="cl-title">Climate context</h3>
    <div class="cl-when">${name}, fire-weighted region average</div>
    ${rows.join("")}
    <p class="cl-note">Difference from the ${s.b0}–${s.b1} ${cal} average, region-wide: weighted average of ${(C.points || []).length || 5} points in the areas of ${state.meta.name_en} with the most fires in 2012–2025.${local} Shown alongside the fire counts, not a causal claim. Source: NASA POWER.</p>`;
}
