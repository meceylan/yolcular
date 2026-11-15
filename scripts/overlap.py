# AI-assisted: generated with Claude (Anthropic)
"""Adım 30: örtüşme dönemi analizi (MODIS ile VIIRS S-NPP, 2012-2025).

1. Aynı hücre ve aylardaki sayılar (kesinti günleri çıkarılmış)
2. Aynı geçiş döneminde ve yakın konumdaki tespitlerin eşleştirilmesi (ikinci kanıt)
Çıktı: data/processed/<bölge>/overlap_cell_month.parquet, docs/overlap_stats.json,
       docs/overlap_scatter.png
Kullanım: python scripts/overlap.py --region turkiye
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, LogNorm

from common import DATA_PROCESSED, DOCS, load_region, region_parser
from filters import GAPS

OVERLAP_START, OVERLAP_END = "2012-02-01", "2025-12-31"
STABLE_LAST = 2022          # Terra ve Aqua geçiş saatleri 2022 sonuna kadar sabit
C_MODIS, C_VIIRS, MUTED, GRID, INK2 = "#2a78d6", "#eb6834", "#898781", "#e1e0d9", "#52514e"
SEQ = LinearSegmentedColormap.from_list("seq", ["#cde2fb", "#86b6ef", "#2a78d6", "#0d366b"])
ZONES = ["Güneydoğu", "İç Anadolu", "Çukurova", "Ege-Akdeniz kıyısı", "Diğer"]


def style():
    plt.rcParams.update({"figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "savefig.facecolor": "#fcfcfb",
                         "axes.edgecolor": "#c3c2b7", "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
                         "text.color": "#0b0b0b", "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                         "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True, "font.size": 9,
                         "axes.titlesize": 10.5, "axes.titleweight": "bold", "axes.titlelocation": "left",
                         "legend.frameon": False, "figure.dpi": 130})


def gap_dates(keys=("SNPP", "MODIS")):
    out = set()
    for k in keys:
        for a, b in GAPS[k]:
            out.update(d.strftime("%Y-%m-%d") for d in pd.date_range(a, b))
    return out


def zone_of(i, j, cell):
    lat, lon = np.asarray(i) * cell - 90 + cell / 2, np.asarray(j) * cell - 180 + cell / 2
    z = np.full(len(lat), "Diğer", dtype=object)
    z[(lat >= 36.5) & (lat <= 38.5) & (lon >= 38) & (lon <= 42.5)] = "Güneydoğu"
    z[(lat >= 38) & (lat <= 40.2) & (lon >= 32) & (lon <= 36.5)] = "İç Anadolu"
    z[(lat >= 36) & (lat <= 38.6) & (lon >= 27) & (lon <= 32.5)] = "Ege-Akdeniz kıyısı"
    z[(lat >= 36) & (lat <= 37.6) & (lon >= 34.5) & (lon <= 37)] = "Çukurova"
    return z


def load_cell_month(region, start=OVERLAP_START, end=OVERLAP_END, drop_gaps=True):
    """Hücre × ay: MODIS (Terra+Aqua) ve S-NPP sayıları, gündüz/gece ayrımıyla."""
    cell = float(region["cell_deg"])
    g = pd.read_parquet(DATA_PROCESSED / region["name"] / "grid_daily.parquet")
    g["acq_date"] = g.acq_date.astype(str)
    g = g[(g.acq_date >= start) & (g.acq_date <= end) & g.satellite.isin(["Terra", "Aqua", "SNPP"])]
    if drop_gaps:
        g = g[~g.acq_date.isin(gap_dates())]
    g = g.assign(ym=g.acq_date.str[:7], s=np.where(g.sensor == "MODIS", "m", "v"))
    t = g.pivot_table(index=["ym", "i", "j"], columns="s", values=["count", "count_day", "count_night"], aggfunc="sum", fill_value=0)
    t.columns = [f"{s}{'' if c == 'count' else '_day' if c == 'count_day' else '_night'}" for c, s in t.columns]
    t = t.reset_index()
    t["y"], t["mo"] = t.ym.str[:4].astype(int), t.ym.str[5:].astype(int)
    t["zone"] = zone_of(t.i, t.j, cell)
    return t


def match_detections(region):
    """Aynı geçiş döneminde (gündüz ya da gece) R km içinde karşı sensör tespiti var mı."""
    cols = ["acq_date", "acq_time", "latitude", "longitude", "sensor", "satellite", "daynight", "keep"]
    d = pd.read_parquet(DATA_PROCESSED / region["name"] / "detections.parquet", columns=cols)
    d = d[d.keep & d.satellite.isin(["Terra", "Aqua", "SNPP"]) & (d.acq_date.astype(str) >= OVERLAP_START)
          & (d.acq_date.astype(str) <= OVERLAP_END)].copy()
    d["acq_date"] = d.acq_date.astype(str)
    d = d[~d.acq_date.isin(gap_dates())]
    t = pd.to_datetime(d.acq_date) + pd.to_timedelta(d.acq_time.str[:2].astype(int) * 60 + d.acq_time.str[2:].astype(int), unit="m")
    d["t_min"] = (t - pd.Timestamp("2012-01-01")).dt.total_seconds() / 60
    d["period"] = np.floor((d.t_min + 9 * 60) / (12 * 60)).astype(np.int64)   # gündüz ve gece geçişleri ayrı kutularda
    d["y"] = d.acq_date.str[:4].astype(int)
    C = 0.04
    d["ci"], d["cj"] = np.floor(d.latitude / C).astype(np.int64), np.floor(d.longitude / C).astype(np.int64)
    d["id"] = np.arange(len(d))
    m, v = d[d.sensor == "MODIS"], d[d.sensor == "VIIRS"]
    best_m = pd.Series(np.inf, index=m.id)   # her MODIS tespiti için en yakın VIIRS (km)
    best_v = pd.Series(np.inf, index=v.id)
    vv = v[["period", "ci", "cj", "id", "latitude", "longitude"]].rename(columns={"id": "vid", "latitude": "vlat", "longitude": "vlon"})
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            mm = m[["period", "ci", "cj", "id", "latitude", "longitude"]].assign(ci=m.ci + di, cj=m.cj + dj)
            p = mm.merge(vv, on=["period", "ci", "cj"])
            if not len(p):
                continue
            dy = (p.latitude - p.vlat) * 111.2
            dx = (p.longitude - p.vlon) * 111.2 * np.cos(np.radians(p.latitude))
            p["km"] = np.hypot(dx, dy)
            best_m = np.minimum(best_m, p.groupby("id").km.min().reindex(best_m.index, fill_value=np.inf))
            best_v = np.minimum(best_v, p.groupby("vid").km.min().reindex(best_v.index, fill_value=np.inf))
    m = m.assign(km=best_m.to_numpy())
    v = v.assign(km=best_v.to_numpy())
    out = {}
    for R in (1.0, 2.0, 3.0):
        out[f"{R:g} km"] = {
            "modis_with_viirs_pct": round(float((m.km <= R).mean() * 100), 1),
            "aqua_with_viirs_pct": round(float((m[m.satellite == "Aqua"].km <= R).mean() * 100), 1),
            "terra_with_viirs_pct": round(float((m[m.satellite == "Terra"].km <= R).mean() * 100), 1),
            "viirs_with_modis_pct": round(float((v.km <= R).mean() * 100), 1),
        }
    R = 2.0
    detail = {"radius_km": R, "n_modis": int(len(m)), "n_viirs": int(len(v))}
    for name, sel_m, sel_v in [("day", m.daynight == "D", v.daynight == "D"), ("night", m.daynight == "N", v.daynight == "N"),
                               ("2012_2022", m.y <= STABLE_LAST, v.y <= STABLE_LAST), ("2023_2025", m.y > STABLE_LAST, v.y > STABLE_LAST)]:
        detail[name] = {"modis_with_viirs_pct": round(float((m[sel_m].km <= R).mean() * 100), 1),
                        "aqua_with_viirs_pct": round(float((m[sel_m & (m.satellite == "Aqua")].km <= R).mean() * 100), 1),
                        "terra_with_viirs_pct": round(float((m[sel_m & (m.satellite == "Terra")].km <= R).mean() * 100), 1),
                        "viirs_with_modis_pct": round(float((v[sel_v].km <= R).mean() * 100), 1)}
    detail["aqua_with_viirs_pct_by_year"] = {int(y): round(float((g.km <= R).mean() * 100), 1) for y, g in m[m.satellite == "Aqua"].groupby("y")}
    detail["terra_with_viirs_pct_by_year"] = {int(y): round(float((g.km <= R).mean() * 100), 1) for y, g in m[m.satellite == "Terra"].groupby("y")}
    detail["viirs_with_modis_pct_by_year"] = {int(y): round(float((g.km <= R).mean() * 100), 1) for y, g in v.groupby("y")}
    return out, detail


def main():
    a = region_parser("Örtüşme dönemi analizi (adım 30)").parse_args()
    region = load_region(a.region)
    style()
    t = load_cell_month(region)
    out_dir = DATA_PROCESSED / region["name"]
    t.to_parquet(out_dir / "overlap_cell_month.parquet", index=False)
    S = {"period": [OVERLAP_START, OVERLAP_END], "gap_days_excluded": len(gap_dates()), "cell_months": int(len(t)),
         "modis_total": int(t.m.sum()), "viirs_total": int(t.v.sum()), "ratio_of_sums": round(float(t.v.sum() / t.m.sum()), 3)}

    def ratio(g):
        return round(float(g.v.sum() / g.m.sum()), 2)

    S["ratio_by_year"] = {int(y): ratio(g) for y, g in t.groupby("y")}
    raw = load_cell_month(region, drop_gaps=False)
    S["ratio_by_year_gaps_included"] = {int(y): ratio(g) for y, g in raw.groupby("y")}
    S["ratio_by_month"] = {int(mo): {"all": ratio(g), "stable_2012_2022": ratio(g[g.y <= STABLE_LAST]), "drift_2023_2025": ratio(g[g.y > STABLE_LAST]),
                                     "modis": int(g.m.sum()), "viirs": int(g.v.sum())} for mo, g in t.groupby("mo")}
    S["ratio_by_zone"] = {z: {"ratio": ratio(g), "modis": int(g.m.sum())} for z, g in t.groupby("zone")}
    S["ratio_day_night"] = {"day": round(float(t.v_day.sum() / t.m_day.sum()), 2), "night": round(float(t.v_night.sum() / t.m_night.sum()), 2),
                            "modis_night_share_pct": round(float(t.m_night.sum() / t.m.sum() * 100), 1),
                            "viirs_night_share_pct": round(float(t.v_night.sum() / t.v.sum() * 100), 1)}
    S["ratio_periods"] = {"stable_2012_2022": ratio(t[t.y <= STABLE_LAST]), "drift_2023_2025": ratio(t[t.y > STABLE_LAST]),
                          "2012_2020": ratio(t[t.y <= 2020]), "2021_2022": ratio(t[t.y.isin([2021, 2022])])}
    # etkinlik düzeyine göre (hücre-ay MODIS sayısı)
    bins = [(0, 0), (1, 1), (2, 4), (5, 9), (10, 19), (20, 49), (50, 10 ** 6)]
    S["by_modis_level"] = {}
    for lo, hi in bins:
        g = t[(t.m >= lo) & (t.m <= hi)]
        S["by_modis_level"][f"{lo}" if lo == hi else f"{lo}-{hi if hi < 10 ** 6 else '+'}"] = {
            "cell_months": int(len(g)), "modis": int(g.m.sum()), "viirs": int(g.v.sum()),
            "viirs_share_pct": round(float(g.v.sum() / t.v.sum() * 100), 1),
            "ratio": None if g.m.sum() == 0 else round(float(g.v.sum() / g.m.sum()), 2)}
    both = t[(t.m > 0) & (t.v > 0)]
    S["cell_month_correlation"] = {"pearson": round(float(t.m.corr(t.v)), 3), "spearman": round(float(t.m.rank().corr(t.v.rank())), 3),
                                   "log_pearson_both_positive": round(float(np.log(both.m).corr(np.log(both.v))), 3),
                                   "cell_months_modis_only": int(((t.m > 0) & (t.v == 0)).sum()),
                                   "cell_months_viirs_only": int(((t.m == 0) & (t.v > 0)).sum()), "cell_months_both": int(len(both))}
    rm = t.groupby(["ym", "y", "mo"])[["m", "v"]].sum().reset_index()
    S["region_month_correlation"] = {"pearson": round(float(rm.m.corr(rm.v)), 3), "log_pearson": round(float(np.log(rm.m).corr(np.log(rm.v))), 3),
                                     "months": int(len(rm))}
    # yıl içi hücre toplamı (hücre × yıl)
    cy = t.groupby(["y", "i", "j"])[["m", "v"]].sum().reset_index()
    S["cell_year_correlation"] = round(float(cy.m.corr(cy.v)), 3)

    radii, detail = match_detections(region)
    S["matching_by_radius"] = radii
    S["matching_detail"] = detail

    # ---------- grafik ----------
    c_all = S["ratio_of_sums"]
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5))
    ax = axes[0]
    hb = ax.hexbin(both.m, both.v, xscale="log", yscale="log", gridsize=34, cmap=SEQ, norm=LogNorm(), mincnt=1, linewidths=0)
    xs = np.array([1, both.m.max()])
    ax.plot(xs, xs * c_all, color="#0b0b0b", lw=1.3, ls="--")
    ax.text(xs[1], xs[1] * c_all, f" V = {c_all:.2f} × M", ha="right", va="bottom", fontsize=8.5)
    ax.set_xlabel("MODIS tespiti (hücre × ay)")
    ax.set_ylabel("VIIRS S-NPP tespiti (hücre × ay)")
    ax.set_title("Aynı hücre ve ay: 0,25° hücreler, 2012–2025")
    fig.colorbar(hb, ax=ax, shrink=0.8, label="Hücre-ay sayısı")
    ax = axes[1]
    st, dr = rm[rm.y <= STABLE_LAST], rm[rm.y > STABLE_LAST]
    ax.scatter(st.m, st.v, s=22, color=C_MODIS, edgecolors="#fcfcfb", linewidths=0.6, label=f"2012–{STABLE_LAST} (yörünge sabit)")
    ax.scatter(dr.m, dr.v, s=22, color=C_VIIRS, edgecolors="#fcfcfb", linewidths=0.6, label="2023–2025 (yörünge kaymış)")
    xs = np.array([rm.m.min(), rm.m.max()])
    ax.plot(xs, xs * c_all, color="#0b0b0b", lw=1.3, ls="--")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("MODIS tespiti (Türkiye × ay)")
    ax.set_ylabel("VIIRS S-NPP tespiti (Türkiye × ay)")
    ax.set_title("Ülke toplamı, aylık")
    ax.legend(loc="upper left", fontsize=8.5)
    fig.tight_layout()
    fig.savefig(DOCS / "overlap_scatter.png")
    plt.close(fig)

    (DOCS / "overlap_stats.json").write_text(json.dumps(S, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(S, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
