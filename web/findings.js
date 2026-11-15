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
  const where = state.full ? regionName(state.region) : t("f.selarea");
  const name = monthName(M.months[idx]), calMonth = MONTHS_LONG[+M.months[idx].slice(5) - 1];
  const partial = M.partial[idx] && M.mtd;
  const lines = [];

  // 1. Selected month against the median of the same calendar month (same numbers as the card).
  const r = partial ? comparePartial() : compareFull(idx);
  const { med, few, pct } = vsMedian(r);
  const est = partial ? harm : isEst(idx);
  const val = t("f.det", { v: fmt(r.value), one: r.value === 1, est });
  const span = partial ? t("f.days", { m: name, d: r.D }) : name;
  if (r.value == null) lines.push(t("f.nodata", { span, where }));
  else if (few) lines.push(t("f.few", { span, val, where, cal: calMonth }));
  else if (pct == null) lines.push(t("f.noother", { span, val, where }));
  else lines.push(t("f.cmp", { span, val, where, n: pctNum(pct), up: pct >= 0, cal: calMonth, days: partial ? r.D : 0, years: r.others.length, med: fmt(med) }));

  // 2. Rank among all complete months in the period.
  const ranked = [];
  for (let k = from; k <= to; k++) if (!M.partial[k] && M[s][k] != null) ranked.push(M[s][k]);
  if (partial) lines.push(t("f.unranked", { d: r.D }));
  else if (r.value != null && ranked.length) {
    const rank = ranked.filter((v) => v > r.value).length + 1;
    lines.push(t("f.rank", { rank: ordinalText(rank), n: LANG === "tr" ? nf(ranked.length) : ranked.length, a: monthName(M.months[from]), b: monthName(M.months[to]), est }));
  }

  // 3. Highest measured month (estimated months are left out: early MODIS-based estimates can be too high).
  let pk = -1;
  for (let k = from; k <= to; k++)
    if (!isEst(k) && !M.partial[k] && M[s][k] != null && (pk < 0 || M[s][k] > M[s][pk])) pk = k;
  if (pk >= 0) lines.push(t(harm ? "f.peakm" : "f.peak", { where, m: monthName(M.months[pk]), v: fmt(M[s][pk]) }));
  else lines.push(t(harm ? "f.nomeash" : "f.nomeas"));

  const exp = state.meta.quality === "experimental";
  box.innerHTML = `<h3 id="findings-title" class="findings-title">${t("f.title")}${exp ? ` <span class="tag">${t("f.exp")}</span>` : ""}</h3>
    <ul class="findings-list">${lines.map((t) => `<li>${t}</li>`).join("")}</ul>
    ${exp ? `<p class="findings-note">${t("f.expnote", { note: cap(qualityNote(state.meta)) })}</p>` : ""}`;
}
