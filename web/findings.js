// AI-assisted: generated with Claude (Anthropic)
// Step 78: "Key findings" box. Three sentences computed from the data shown (region or drawn area,
// series, period, selected month). Uses the same comparison as the summary card (compareFull/comparePartial,
// vsMedian in app.js). States what the data show, no causes. Loaded before app.js; uses its globals at call time.
"use strict";

function ordinal(n) {
  const s = ["th", "st", "nd", "rd"], v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

const cap = (t) => t.charAt(0).toUpperCase() + t.slice(1);

function drawFindings() {
  const box = $("findings");
  if (!box || !state.cur || state.cmpIdx == null || state.cmpIdx < 0) return;
  const M = state.cur, s = state.series, idx = state.cmpIdx, { from, to } = state.range;
  const harm = state.meta.harmonized && s === "h";
  const isEst = (k) => harm && M.src[k] !== "V";
  const where = state.full ? state.meta.name_en : "the selected area";
  const name = monthName(M.months[idx]), calMonth = MONTHS_LONG[+M.months[idx].slice(5) - 1];
  const partial = M.partial[idx] && M.mtd;
  const lines = [];

  // 1. Selected month against the median of the same calendar month (same numbers as the card).
  const r = partial ? comparePartial() : compareFull(idx);
  const { med, few, pct } = vsMedian(r);
  const est = partial ? harm : isEst(idx);
  const val = `${fmt(r.value)} fire detection${r.value === 1 ? "" : "s"}${est ? " (estimated)" : ""}`;
  const span = partial ? `${name}, days 1–${r.D}` : name;
  if (r.value == null) lines.push(`${span}: no data for this series in ${where}.`);
  else if (few) lines.push(`${span}: ${val} in ${where}; too few detections in a typical ${calMonth} for a percentage.`);
  else if (pct == null) lines.push(`${span}: ${val} in ${where}; no other years in the period to compare with.`);
  else lines.push(`${span}: ${val} in ${where}, ${Math.abs(pct).toFixed(0)}% ${pct >= 0 ? "above" : "below"} the median ${calMonth}${partial ? ` (days 1–${r.D})` : ""} of ${r.others.length} other years (${fmt(med)}).`);

  // 2. Rank among all complete months in the period.
  const ranked = [];
  for (let k = from; k <= to; k++) if (!M.partial[k] && M[s][k] != null) ranked.push(M[s][k]);
  if (partial) lines.push(`The month is not finished yet (data through day ${r.D}), so it is not ranked.`);
  else if (r.value != null && ranked.length) {
    const rank = ranked.filter((v) => v > r.value).length + 1;
    lines.push(`It ranks ${ordinal(rank)} of ${ranked.length} complete months (${monthName(M.months[from])} – ${monthName(M.months[to])})${est ? "; its value is an estimate" : ""}.`);
  }

  // 3. Highest measured month (estimated months are left out: early MODIS-based estimates can be too high).
  let pk = -1;
  for (let k = from; k <= to; k++)
    if (!isEst(k) && !M.partial[k] && M[s][k] != null && (pk < 0 || M[s][k] > M[s][pk])) pk = k;
  if (pk >= 0) lines.push(`${harm ? "Highest measured month" : "Highest month"} in ${where}${harm ? " (VIIRS, from February 2012)" : ""}: ${monthName(M.months[pk])}, ${fmt(M[s][pk])} detections.`);
  else lines.push(`No measured months in the selected period${harm ? ": all values before February 2012 are estimates" : ""}.`);

  const exp = state.meta.quality === "experimental";
  box.innerHTML = `<h3 id="findings-title" class="findings-title">Key findings${exp ? ' <span class="tag">experimental</span>' : ""}</h3>
    <ul class="findings-list">${lines.map((t) => `<li>${t}</li>`).join("")}</ul>
    ${exp ? `<p class="findings-note">Experimental region. ${cap(state.meta.quality_note || "values before 2012 are rough.")}</p>` : ""}`;
}
