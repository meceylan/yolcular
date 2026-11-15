# AI-assisted: generated with Claude (Anthropic)
"""Adım 50: Seviye 2 bölgeleri için harmonizasyon kararlarının sayısal dayanağı.

- Sabit kaynak kontrolü (mevsimsellik, kalıcılık, Nil deltası)
- Katsayı seçenekleri, bir yılı dışarıda bırakarak sınama
- NOAA-20 katsayısı seçenekleri
- MODIS başlangıç tarihi, Türkiye ile kesişen alan
Çıktı: docs/s2_stats.json
Kullanım: python scripts/s2_decide.py
"""
import json

import numpy as np
import pandas as pd

from common import DATA_PROCESSED, DOCS, load_region
from overlap import STABLE_LAST, gap_dates

REGIONS = ["balkanlar", "kafkasya", "dogu_akdeniz", "turkiye"]
SEASON = {12: "DJF", 1: "DJF", 2: "DJF", 3: "MAM", 4: "MAM", 5: "MAM", 6: "JJA", 7: "JJA", 8: "JJA", 9: "SON", 10: "SON", 11: "SON"}
LAMBDAS = (100, 300, 1000)


def month_table(name, sats=("Terra", "Aqua", "SNPP"), start="2012-02-01", end="2025-12-31", gaps=("SNPP", "MODIS")):
    g = pd.read_parquet(DATA_PROCESSED / name / "grid_daily.parquet")
    g["acq_date"] = g.acq_date.astype(str)
    g = g[(g.acq_date >= start) & (g.acq_date <= end) & g.satellite.isin(sats) & ~g.acq_date.isin(gap_dates(gaps))]
    g = g.assign(y=g.acq_date.str[:4].astype(int), mo=g.acq_date.str[5:7].astype(int),
                 s=np.where(g.sensor == "MODIS", "m", np.where(g.satellite == "SNPP", "v", "n")))
    t = g.pivot_table(index=["y", "mo"], columns="s", values="count", aggfunc="sum", fill_value=0).reset_index()
    full = pd.MultiIndex.from_product([sorted(t.y.unique()), range(1, 13)], names=["y", "mo"])
    return t.set_index(["y", "mo"]).reindex(full, fill_value=0).reset_index()


# ---- katsayı seçenekleri: eğitim tablosu -> 12 aylık katsayı serisi ----
def c_monthly(tr, **_):
    g = tr.groupby("mo")[["m", "v"]].sum()
    return (g.v / g.m).reindex(range(1, 13))


def c_seasonal(tr, **_):
    g = tr.assign(se=tr.mo.map(SEASON)).groupby("se")[["m", "v"]].sum()
    r = g.v / g.m
    return pd.Series({mo: r[SEASON[mo]] for mo in range(1, 13)})


def c_constant(tr, **_):
    return pd.Series(tr.v.sum() / tr.m.sum(), index=range(1, 13))


def c_shrunk(tr, lam=300, **_):
    c0 = tr.v.sum() / tr.m.sum()
    g = tr.groupby("mo")[["m", "v"]].sum().reindex(range(1, 13), fill_value=0)
    return (g.v + lam * c0) / (g.m + lam)


def c_turkiye(tr, c_tr=None, **_):
    return c_tr


def c_turkiye_scaled(tr, c_tr=None, **_):
    return c_tr * (tr.v.sum() / (tr.m * c_tr.reindex(tr.mo).to_numpy()).sum())


def score(t, fn, **kw):
    cal = t[t.y <= STABLE_LAST]
    parts = []
    for y in sorted(cal.y.unique()):
        c = fn(cal[cal.y != y], **kw)
        te = cal[cal.y == y]
        parts.append(te.assign(pred=te.m * c.reindex(te.mo).to_numpy()))
    cv = pd.concat(parts)
    ry = cv.groupby("y")[["v", "pred"]].sum()
    c = fn(cal, **kw)
    dr = t[t.y > STABLE_LAST]
    dr = dr.assign(pred=dr.m * c.reindex(dr.mo).to_numpy())
    dy = dr.groupby("y")[["v", "pred"]].sum()
    ok = cv[cv.pred > 0]
    q = ok.v / ok.pred
    return {
        "month_weighted_abs_err_pct": round(float((cv.pred - cv.v).abs().sum() / cv.v.sum() * 100), 1),
        "month_median_abs_err_pct": round(float(((cv.pred - cv.v).abs() / cv.v.replace(0, np.nan)).median() * 100), 1),
        "year_mean_abs_err_pct": round(float(((ry.pred - ry.v).abs() / ry.v).mean() * 100), 1),
        "year_max_abs_err_pct": round(float(((ry.pred - ry.v).abs() / ry.v).max() * 100), 1),
        "test_2023_2025_month_weighted_abs_err_pct": round(float((dr.pred - dr.v).abs().sum() / dr.v.sum() * 100), 1),
        "test_2023_2025_total_err_pct": round(float((dy.pred.sum() - dy.v.sum()) / dy.v.sum() * 100), 1),
        "test_2023_2025_year_err_pct": {int(y): round(float((r.pred - r.v) / r.v * 100), 1) for y, r in dy.iterrows()},
        "p16_p84": [round(float(q.quantile(0.16)), 2), round(float(q.quantile(0.84)), 2)],
    }, cv


def static_check(name):
    cols = ["acq_date", "latitude", "longitude", "sensor", "satellite", "daynight", "type", "frp", "in_country", "keep", "is_nrt",
            "flag_static", "flag_low_conf", "confidence_class"]
    d = pd.read_parquet(DATA_PROCESSED / name / "detections.parquet", columns=cols)
    d["acq_date"] = d.acq_date.astype(str)
    d = d[d.in_country & ~d.is_nrt & (d.satellite == "SNPP") & (d.acq_date >= "2012-02-01") & (d.acq_date <= "2025-12-31")].copy()
    d["mo"], d["y"] = d.acq_date.str[5:7].astype(int), d.acq_date.str[:4].astype(int)
    d["cell"] = np.floor(d.latitude / 0.01).astype(np.int64) * 100000 + np.floor((d.longitude + 180) / 0.01).astype(np.int64)
    per = d.groupby("cell").agg(days=("acq_date", "nunique"), years=("y", "nunique"), cal_months=("mo", "nunique"))
    d = d.join(per, on="cell")
    st, fi = d[d.type == 2], d[d.type == 0]

    def season(x):
        s = x.groupby("mo").size().reindex(range(1, 13), fill_value=0)
        return {"share_pct": [round(float(v), 1) for v in (s / s.sum() * 100)], "peak_over_mean": round(float(s.max() / s.mean()), 2)}

    def persist(x):
        return {"n": int(len(x)), "night_pct": round(float((x.daynight == "N").mean() * 100), 1), "frp_median": round(float(x.frp.median()), 2),
                "in_cells_ge30days_ge10calmonths_pct": round(float(((x.days >= 30) & (x.cal_months >= 10)).mean() * 100), 1),
                "in_cells_ge10years_pct": round(float((x.years >= 10).mean() * 100), 1),
                "in_cells_le3days_pct": round(float((x.days <= 3).mean() * 100), 1),
                "median_days_of_cell": float(x.days.median()), "season": season(x)}
    out = {"viirs_land_total": int(len(d)), "static_share_pct": round(float(len(st) / len(d) * 100), 1),
           "static": persist(st), "fire_type0": persist(fi), "fire_kept": persist(d[d.keep])}
    # şüpheli elenenler: sabit kaynak işaretli ama kalıcı olmayan (en çok 3 gün görülmüş hücre) tespitler
    sus = st[st.days <= 3]
    out["static_nonpersistent"] = {"n": int(len(sus)), "share_of_static_pct": round(float(len(sus) / max(len(st), 1) * 100), 1),
                                   "share_of_kept_fire_pct": round(float(len(sus) / max(int(d.keep.sum()), 1) * 100), 1),
                                   "season": season(sus) if len(sus) else None}
    # şüpheli tutulanlar: yangın sayılan ama çok kalıcı hücrelerdeki tespitler
    leak = d[d.keep & (d.days >= 30) & (d.cal_months >= 10)]
    out["kept_but_persistent"] = {"n": int(len(leak)), "share_of_kept_pct": round(float(len(leak) / max(int(d.keep.sum()), 1) * 100), 1),
                                  "cells": int(leak.cell.nunique()), "night_pct": round(float((leak.daynight == "N").mean() * 100), 1) if len(leak) else None}
    if name == "dogu_akdeniz":
        nile = d.latitude.between(30.0, 31.7) & d.longitude.between(30.0, 32.4)
        out["nile_delta"] = {"static": persist(d[nile & (d.type == 2)]), "fire_type0": persist(d[nile & (d.type == 0)]),
                             "static_share_pct": round(float((nile & (d.type == 2)).sum() / nile.sum() * 100), 1),
                             "share_of_region_static_pct": round(float((nile & (d.type == 2)).sum() / len(st) * 100), 1)}
        top = st.groupby("cell").agg(n=("acq_date", "size"), days=("days", "first"), years=("years", "first"), lat=("latitude", "mean"),
                                     lon=("longitude", "mean"), night=("daynight", lambda s: round(float((s == "N").mean() * 100)))).sort_values("n", ascending=False)
        top["blk"] = (top.lat.round(1)).astype(str) + "," + (top.lon.round(1)).astype(str)
        b = top.groupby("blk").agg(n=("n", "sum"), cells=("n", "size"), max_days=("days", "max")).sort_values("n", ascending=False).head(12)
        out["top_static_clusters_0.1deg"] = {k: {"detections": int(r.n), "cells": int(r.cells), "max_days": int(r.max_days)} for k, r in b.iterrows()}
        out["static_in_top12_clusters_pct"] = round(float(b.n.sum() / len(st) * 100), 1)
    return out


def main():
    S = {}
    tabs = {r: month_table(r) for r in REGIONS}
    c_tr = c_monthly(tabs["turkiye"][tabs["turkiye"].y <= STABLE_LAST])
    for r in REGIONS:
        t = tabs[r]
        cal = t[t.y <= STABLE_LAST]
        res = {"modis_cal_total": int(cal.m.sum()), "viirs_cal_total": int(cal.v.sum()), "ratio": round(float(cal.v.sum() / cal.m.sum()), 2),
               "modis_per_month_min": int(cal.groupby("mo").m.sum().min()), "ratio_by_year": {int(y): round(float(g.v.sum() / g.m.sum()), 2) for y, g in t.groupby("y")},
               "options": {}}
        opts = [("kendi aylık (12)", c_monthly, {}), ("kendi mevsimlik (4)", c_seasonal, {}), ("kendi sabit (1)", c_constant, {}),
                ("Türkiye aylık (0)", c_turkiye, {"c_tr": c_tr}), ("Türkiye aylık × bölge ölçeği (1)", c_turkiye_scaled, {"c_tr": c_tr})]
        opts += [(f"kendi aylık, sabite çekilmiş λ={lam}", c_shrunk, {"lam": lam}) for lam in LAMBDAS]
        for name, fn, kw in opts:
            res["options"][name], _ = score(t, fn, **kw)
        res["coef_monthly"] = {int(k): round(float(v), 2) for k, v in c_monthly(cal).items()}
        res["coef_shrunk_300"] = {int(k): round(float(v), 2) for k, v in c_shrunk(cal, 300).items()}
        res["coef_seasonal"] = {int(k): round(float(v), 2) for k, v in c_seasonal(cal).items()}
        # NOAA-20
        n = month_table(r, sats=("SNPP", "NOAA20"), start="2023-01-01", gaps=("SNPP",))
        k = {"own_constant": round(float(n.v.sum() / n.n.sum()), 3), "by_year": {int(y): round(float(g.v.sum() / g.n.sum()), 3) for y, g in n.groupby("y")}}
        err = {}
        for lab, kk in [("own (leave-one-year-out)", None), ("1.000", 1.0), ("turkiye 0.986", 0.986), ("pooled", "pooled")]:
            e = []
            for y in sorted(n.y.unique()):
                te = n[n.y == y]
                if kk is None:
                    tr = n[n.y != y]
                    kv = tr.v.sum() / tr.n.sum()
                elif kk == "pooled":
                    alln = pd.concat([month_table(x, sats=("SNPP", "NOAA20"), start="2023-01-01", gaps=("SNPP",)) for x in REGIONS])
                    alln = alln[alln.y != y]
                    kv = alln.v.sum() / alln.n.sum()
                else:
                    kv = kk
                e.append((te.n * kv - te.v).abs().sum() / te.v.sum())
            err[lab] = round(float(np.mean(e) * 100), 1)
        k["month_weighted_abs_err_pct"] = err
        res["noaa20"] = k
        S[r] = res
    alln = pd.concat([month_table(x, sats=("SNPP", "NOAA20"), start="2023-01-01", gaps=("SNPP",)) for x in REGIONS])
    S["noaa20_pooled_k"] = round(float(alln.v.sum() / alln.n.sum()), 3)

    for r in ["dogu_akdeniz", "balkanlar", "kafkasya", "turkiye"]:
        S[r]["static_check"] = static_check(r)

    # MODIS başlangıcı: 1–8 Temmuz 2002, uydu ve güne göre (Türkiye tablosu; bölgelerde 4 Temmuz öncesi atılmış)
    d = pd.read_parquet(DATA_PROCESSED / "turkiye" / "detections.parquet", columns=["acq_date", "satellite", "sensor", "keep", "in_country"])
    d["acq_date"] = d.acq_date.astype(str)
    j = d[(d.sensor == "MODIS") & (d.acq_date <= "2002-07-10")]
    S["modis_start_turkiye"] = {"all_rows_by_day_sat": {f"{a} {b}": int(n) for (a, b), n in j.groupby(["acq_date", "satellite"]).size().items()},
                                "kept_before_0704": int((j.keep & (j.acq_date < "2002-07-04")).sum()),
                                "kept_july_2002": int((d.keep & (d.sensor == "MODIS") & d.acq_date.str.startswith("2002-07")).sum())}

    # Türkiye ile kesişen alan: Türkiye ızgarasındaki hücrelerden bölge kutusuna düşenler, MODIS dönemi
    tg = pd.read_parquet(DATA_PROCESSED / "turkiye" / "grid_daily.parquet")
    tg["acq_date"] = tg.acq_date.astype(str)
    tg = tg[(tg.sensor == "MODIS") & (tg.acq_date < "2012-02-01")]
    tg = tg.assign(lat=tg.i * 0.25 - 90 + 0.125, lon=tg.j * 0.25 - 180 + 0.125, mo=tg.acq_date.str[5:7].astype(int), y=tg.acq_date.str[:4].astype(int))
    S["overlap_with_turkiye"] = {}
    for r in REGIONS[:3]:
        b = load_region(r)["bbox"]
        x = tg[tg.lat.between(b["south"], b["north"]) & tg.lon.between(b["west"], b["east"])]
        own = c_monthly(tabs[r][tabs[r].y <= STABLE_LAST])
        sh = c_shrunk(tabs[r][tabs[r].y <= STABLE_LAST], 300)
        h_tr = (x["count"] * c_tr.reindex(x.mo).to_numpy())
        h_own = (x["count"] * own.reindex(x.mo).to_numpy())
        h_sh = (x["count"] * sh.reindex(x.mo).to_numpy())
        rg = pd.read_parquet(DATA_PROCESSED / r / "grid_daily.parquet")
        rg["acq_date"] = rg.acq_date.astype(str)
        rm = rg[(rg.sensor == "MODIS") & (rg.acq_date < "2012-02-01")]["count"].sum()
        by = pd.DataFrame({"tr": h_tr.groupby(x.y).sum(), "own": h_own.groupby(x.y).sum()})
        S["overlap_with_turkiye"][r] = {
            "turkiye_cells_in_box": int(x[["i", "j"]].drop_duplicates().shape[0]), "modis_2002_2011_in_overlap": int(x["count"].sum()),
            "share_of_region_modis_pct": round(float(x["count"].sum() / rm * 100), 1),
            "share_of_turkiye_modis_pct": round(float(x["count"].sum() / tg["count"].sum() * 100), 1),
            "h_with_turkiye_coef": round(float(h_tr.sum())), "h_with_region_monthly_coef": round(float(h_own.sum())),
            "diff_region_vs_turkiye_pct": round(float((h_own.sum() / h_tr.sum() - 1) * 100), 1),
            "diff_region_shrunk_vs_turkiye_pct": round(float((h_sh.sum() / h_tr.sum() - 1) * 100), 1),
            "diff_by_year_pct_min_max": [round(float(((by.own / by.tr - 1) * 100).min()), 1), round(float(((by.own / by.tr - 1) * 100).max()), 1)]}

    (DOCS / "s2_stats.json").write_text(json.dumps(S, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(S, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
