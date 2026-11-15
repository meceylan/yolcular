# AI-assisted: generated with Claude (Anthropic)
"""Adım 31: uyumlaştırma katsayıları ve uyumlu seri.

Uyumlu değer = "VIIRS S-NPP eşdeğeri tespit sayısı" (veri sözleşmesi K2):
  - 1 Şubat 2012'den önce      : MODIS sayısı × c[ay]                      (src = M, tahmin)
  - 1 Şub 2012 – 31 Eki 2026   : S-NPP sayısı                              (src = V, ölçüm)
  - 1 Kasım 2026'dan itibaren  : NOAA-20 sayısı × k_N20                    (src = N, tahmin)
Katsayılar "toplamların oranı"dır: c = ΣVIIRS / ΣMODIS, yörüngenin sabit olduğu
2012–2022 yıllarından, kesinti günleri çıkarılarak, her takvim ayı için ayrı (12 sayı).
Gündüz/gece ve alt bölge ayrımı sınandı, tahmini iyileştirmediği için kullanılmadı (docs/harmonize.md).

Çıktı: data/processed/<bölge>/coefficients.json, harmonized_daily.parquet, harmonized_monthly.csv
       docs/coefficients.json (kopya), docs/harmonize_stats.json (model sınaması)
Kullanım: python scripts/harmonize.py --region turkiye

Bölgeye özel ayarlar data/regions.json içindeki "harmonize" alanından okunur (adım 50, docs/harmonize_s2.md):
  modis_method: "monthly" (varsayılan) ya da "shrunk" (az verili aylar bölgenin yıllık oranına çekilir, shrink_lambda)
  k_n20: verilirse NOAA-20 katsayısı bu sabittir (tüm bölgelerde ortak 0,986)
Türkiye dışındaki bölgelerin belgeleri docs/coefficients_<bölge>.json ve docs/harmonize_stats_<bölge>.json olarak yazılır.
"""
import json
from datetime import date

import numpy as np
import pandas as pd

from common import DATA_PROCESSED, DOCS, load_region, region_parser
from filters import gap_days_by_month
from overlap import OVERLAP_END, OVERLAP_START, STABLE_LAST, gap_dates, load_cell_month

VIIRS_START = "2012-02-01"      # Ocak 2012 MODIS'ten (S-NPP 20 Ocak'ta başlıyor)
N20_START = "2026-11-01"
N20_YEARS = (2023, 2025)
PARTS = ("day", "night")


# ---------- katsayı ----------
def fit(t, keys):
    """t: hücre-ay tablosu. keys: gruplama sütunları. Dönen: {anahtar: {'day': c, 'night': c, 'all': c}}"""
    g = t.groupby(keys)[["m", "v", "m_day", "v_day", "m_night", "v_night"]].sum()
    out = pd.DataFrame({"all": g.v / g.m, "day": g.v_day / g.m_day, "night": g.v_night / g.m_night})
    return out


def predict(t, coef, keys, split):
    """Hücre-ay tablosuna tahmin sütunu ekler (doğrusal)."""
    c = coef.reindex(pd.MultiIndex.from_frame(t[keys]) if len(keys) > 1 else t[keys[0]])
    if split:
        return (t.m_day.to_numpy() * np.nan_to_num(c["day"].to_numpy(), posinf=0)
                + t.m_night.to_numpy() * np.nan_to_num(c["night"].to_numpy(), posinf=0))
    return t.m.to_numpy() * np.nan_to_num(c["all"].to_numpy(), posinf=0)


MODELS = {
    "A sabit": (["one"], False),
    "B ay": (["mo"], False),
    "C ay + gündüz/gece": (["mo"], True),
    "D ay + alt bölge": (["mo", "zone"], False),
}
CHOSEN = "B ay"


def evaluate(t):
    """Bir yılı dışarıda bırakarak sınama (2012–2022) ve 2023–2025 bağımsız sınaması."""
    t = t.assign(one=1)
    cal = t[t.y <= STABLE_LAST]
    res = {}
    for name, (keys, split) in MODELS.items():
        parts = []
        for y in sorted(cal.y.unique()):
            coef = fit(cal[cal.y != y], keys)
            test = cal[cal.y == y]
            parts.append(test.assign(pred=predict(test, coef, keys, split)))
        cv = pd.concat(parts)
        cv["pred"] = cv.pred.fillna(0)
        rm = cv.groupby(["y", "mo"])[["v", "pred"]].sum()
        ry = cv.groupby("y")[["v", "pred"]].sum()
        rz = cv.groupby(["y", "mo", "zone"])[["v", "pred"]].sum()
        rz = rz[rz.v >= 50]
        coef = fit(cal, keys)
        dr = t[t.y > STABLE_LAST]
        dr = dr.assign(pred=np.nan_to_num(predict(dr, coef, keys, split)))
        dm = dr.groupby(["y", "mo"])[["v", "pred"]].sum()
        dy = dr.groupby("y")[["v", "pred"]].sum()
        res[name] = {
            "month_median_abs_err_pct": round(float(((rm.pred - rm.v).abs() / rm.v).median() * 100), 1),
            "month_weighted_abs_err_pct": round(float((rm.pred - rm.v).abs().sum() / rm.v.sum() * 100), 1),
            "year_mean_abs_err_pct": round(float(((ry.pred - ry.v).abs() / ry.v).mean() * 100), 1),
            "year_max_abs_err_pct": round(float(((ry.pred - ry.v).abs() / ry.v).max() * 100), 1),
            "zone_month_weighted_abs_err_pct": round(float((rz.pred - rz.v).abs().sum() / rz.v.sum() * 100), 1),
            "test_2023_2025_month_weighted_abs_err_pct": round(float((dm.pred - dm.v).abs().sum() / dm.v.sum() * 100), 1),
            "test_2023_2025_year_err_pct": {int(y): round(float((r.pred - r.v) / r.v * 100), 1) for y, r in dy.iterrows()},
            "test_2023_2025_total_err_pct": round(float((dy.pred.sum() - dy.v.sum()) / dy.v.sum() * 100), 1),
        }
        if name == CHOSEN:
            keep_cv = (cv, rm, ry)
    return res, keep_cv


def c_shrunk(tm, lam):
    """Aylık katsayı, az verili aylarda bölgenin yıllık oranına çekilmiş: (ΣV_ay + λ·c0) / (ΣM_ay + λ)."""
    c0 = tm.v.sum() / tm.m.sum()
    g = tm.groupby("mo")[["m", "v"]].sum().reindex(range(1, 13), fill_value=0)
    return (g.v + lam * c0) / (g.m + lam)


def shrunk_fit_and_cv(t, lam):
    """Çekilmiş aylık katsayı ve bölge × ay düzeyinde bir yılı dışarıda bırakarak sınama."""
    tm = t.groupby(["y", "mo"])[["m", "v"]].sum().reset_index()
    cal = tm[tm.y <= STABLE_LAST]
    parts = []
    for y in sorted(cal.y.unique()):
        c = c_shrunk(cal[cal.y != y], lam)
        te = cal[cal.y == y]
        parts.append(te.assign(pred=te.m * c.reindex(te.mo).to_numpy()))
    cv = pd.concat(parts)
    rm = cv[cv.pred > 0].set_index(["y", "mo"])[["v", "pred"]]
    ry = cv.groupby("y")[["v", "pred"]].sum()
    coef = pd.DataFrame({"all": c_shrunk(cal, lam)})
    dr = tm[tm.y > STABLE_LAST]
    dr = dr.assign(pred=dr.m * coef["all"].reindex(dr.mo).to_numpy())
    dy = dr.groupby("y")[["v", "pred"]].sum()
    summary = {
        "month_median_abs_err_pct": round(float(((rm.pred - rm.v).abs() / rm.v.replace(0, np.nan)).median() * 100), 1),
        "month_weighted_abs_err_pct": round(float((cv.pred - cv.v).abs().sum() / cv.v.sum() * 100), 1),
        "year_mean_abs_err_pct": round(float(((ry.pred - ry.v).abs() / ry.v).mean() * 100), 1),
        "year_max_abs_err_pct": round(float(((ry.pred - ry.v).abs() / ry.v).max() * 100), 1),
        "test_2023_2025_month_weighted_abs_err_pct": round(float((dr.pred - dr.v).abs().sum() / dr.v.sum() * 100), 1),
        "test_2023_2025_year_err_pct": {int(y): round(float((r.pred - r.v) / r.v * 100), 1) for y, r in dy.iterrows()},
        "test_2023_2025_total_err_pct": round(float((dy.pred.sum() - dy.v.sum()) / dy.v.sum() * 100), 1),
    }
    return coef, pd.DataFrame({"all": c_shrunk(tm, lam)}), cv, rm, ry, summary


def uncertainty(rm):
    """Sınamadaki aylık (gerçek / tahmin) dağılımından belirsizlik aralığı."""
    q = (rm.v / rm.pred)
    big = rm.v >= 500
    return {"p16": round(float(q.quantile(0.16)), 2), "p84": round(float(q.quantile(0.84)), 2),
            "p05": round(float(q.quantile(0.05)), 2), "p95": round(float(q.quantile(0.95)), 2),
            "p16_busy_months": round(float(q[big].quantile(0.16)), 2), "p84_busy_months": round(float(q[big].quantile(0.84)), 2)}


def level_effect(cv):
    """Etkinlik düzeyi arttıkça tahmin fazla mı kalıyor? (ülke × ay, o ayın kendi medyanına göre)"""
    rm = cv.groupby(["y", "mo"])[["m", "v", "pred"]].sum().reset_index()
    rm["rel"] = rm.m / rm.groupby("mo").m.transform("median")
    out = {}
    for lab, sel in [("lt_0.5x", rm.rel < 0.5), ("0.5_1.5x", rm.rel.between(0.5, 1.5)), ("1.5_2.5x", (rm.rel > 1.5) & (rm.rel <= 2.5)), ("gt_2.5x", rm.rel > 2.5)]:
        g = rm[sel]
        out[lab] = {"months": int(len(g)), "actual_over_predicted": None if not len(g) else round(float(g.v.sum() / g.pred.sum()), 2)}
    return out


# ---------- NOAA-20 ----------
def n20_table(region):
    g = pd.read_parquet(DATA_PROCESSED / region["name"] / "grid_daily.parquet")
    g["acq_date"] = g.acq_date.astype(str)
    g = g[g.satellite.isin(["SNPP", "NOAA20"]) & (g.acq_date >= f"{N20_YEARS[0]}-01-01") & (g.acq_date <= f"{N20_YEARS[1]}-12-31")]
    g = g[~g.acq_date.isin(gap_dates(("SNPP",)))]
    t = g.assign(y=g.acq_date.str[:4].astype(int), mo=g.acq_date.str[5:7].astype(int)).pivot_table(
        index=["y", "mo"], columns="satellite", values=["count", "count_day", "count_night"], aggfunc="sum", fill_value=0)
    t.columns = [f"{s}_{c}" for c, s in t.columns]
    return t.reset_index()


def fit_n20(t):
    k_all = float(t.SNPP_count.sum() / t.NOAA20_count.sum())
    by_mo = (t.groupby("mo").SNPP_count.sum() / t.groupby("mo").NOAA20_count.sum())
    stats = {"snpp_total": int(t.SNPP_count.sum()), "noaa20_total": int(t.NOAA20_count.sum()), "k_constant": round(k_all, 3),
             "k_by_year": {int(y): round(float(g.SNPP_count.sum() / g.NOAA20_count.sum()), 3) for y, g in t.groupby("y")},
             "k_by_month": {int(mo): round(float(v), 3) for mo, v in by_mo.items()},
             "k_day": round(float(t.SNPP_count_day.sum() / t.NOAA20_count_day.sum()), 3),
             "k_night": round(float(t.SNPP_count_night.sum() / t.NOAA20_count_night.sum()), 3)}
    # bir yılı dışarıda bırak: sabit mi, ay bazında mı
    err = {"constant": [], "by_month": []}
    for y in sorted(t.y.unique()):
        tr, te = t[t.y != y], t[t.y == y]
        kc = tr.SNPP_count.sum() / tr.NOAA20_count.sum()
        km = (tr.groupby("mo").SNPP_count.sum() / tr.groupby("mo").NOAA20_count.sum()).reindex(te.mo).to_numpy()
        err["constant"].append((te.NOAA20_count * kc - te.SNPP_count).abs().sum() / te.SNPP_count.sum())
        err["by_month"].append((te.NOAA20_count * km - te.SNPP_count).abs().sum() / te.SNPP_count.sum())
    stats["cv_month_weighted_abs_err_pct"] = {k: round(float(np.mean(v) * 100), 1) for k, v in err.items()}
    q = t.SNPP_count / (t.NOAA20_count * k_all)
    stats["monthly_actual_over_predicted_p16_p84"] = [round(float(q.quantile(0.16)), 2), round(float(q.quantile(0.84)), 2)]
    return stats, by_mo


# ---------- seri ----------
def build_series(region, coef, k_n20):
    """Hücre × gün: h (uyumlu), m (ham MODIS), v (serinin VIIRS uydusunun ham sayısı), src."""
    g = pd.read_parquet(DATA_PROCESSED / region["name"] / "grid_daily.parquet")
    g["acq_date"] = g.acq_date.astype(str)
    g["mo"] = g.acq_date.str[5:7].astype(int)
    is_m = g.sensor == "MODIS"
    era_m, era_n = g.acq_date < VIIRS_START, g.acq_date >= N20_START
    era_v = ~era_m & ~era_n
    cm = coef["all"].reindex(g.mo).to_numpy()
    kn = k_n20.reindex(g.mo).to_numpy()
    h = np.zeros(len(g))
    sel = is_m & era_m
    h[sel] = (g["count"] * cm)[sel]
    sel = (g.satellite == "SNPP") & era_v
    h[sel] = g["count"][sel]
    sel = (g.satellite == "NOAA20") & era_n
    h[sel] = (g["count"] * kn)[sel]
    g["h"] = h
    g["m"] = np.where(is_m, g["count"], 0)
    g["v"] = np.where(((g.satellite == "SNPP") & era_v) | ((g.satellite == "NOAA20") & era_n), g["count"], 0)
    g["m_day"] = np.where(is_m, g.count_day, 0)
    g["m_night"] = np.where(is_m, g.count_night, 0)
    d = g.groupby(["acq_date", "i", "j"])[["h", "m", "v", "m_day", "m_night"]].sum().reset_index()
    d = d[(d.h > 0) | (d.m > 0) | (d.v > 0)]
    d["src"] = np.where(d.acq_date < VIIRS_START, "M", np.where(d.acq_date >= N20_START, "N", "V"))
    d["h"] = d.h.round(3)
    return d


def main():
    a = region_parser("Uyumlaştırma katsayıları ve uyumlu seri (adım 31)").parse_args()
    region = load_region(a.region)
    out_dir = DATA_PROCESSED / region["name"]
    cfg = region.get("harmonize", {})
    method = cfg.get("modis_method", "monthly")
    suffix = "" if region["name"] == "turkiye" else f"_{region['name']}"
    t = load_cell_month(region)
    t.to_parquet(out_dir / "overlap_cell_month.parquet", index=False)
    cal = t[t.y <= STABLE_LAST]

    # 1. model sınaması
    models, (cv, rm, ry) = evaluate(t)
    coef = fit(cal, ["mo"])                       # seçilen model: B (aya göre tek katsayı)
    coef_all_years = fit(t, ["mo"])
    method_text = "ratio of sums (sum VIIRS S-NPP / sum MODIS), one coefficient per calendar month; gap days excluded"
    if method == "shrunk":
        lam = cfg.get("shrink_lambda", 300)
        coef, coef_all_years, cv, rm, ry, summary = shrunk_fit_and_cv(t, lam)
        models[f"seçilen: aylık, yıllık orana çekilmiş (λ={lam})"] = summary
        method_text = (f"ratio of sums per calendar month, shrunk toward the region's all-year ratio: "
                       f"(sum VIIRS + {lam} x c0) / (sum MODIS + {lam}); gap days excluded")
    unc = uncertainty(rm)
    lvl = level_effect(cv)

    # 2. NOAA-20
    n20_stats, k_by_mo = fit_n20(n20_table(region))
    k_const = pd.Series(n20_stats["k_constant"], index=range(1, 13))
    # ay bazında k yalnızca hatayı en az 1 puan düşürüyorsa kullanılır (basit olan yeğlenir)
    use_monthly_k = n20_stats["cv_month_weighted_abs_err_pct"]["by_month"] < n20_stats["cv_month_weighted_abs_err_pct"]["constant"] - 1.0
    k_used = k_by_mo if use_monthly_k else k_const
    if "k_n20" in cfg:                            # tüm bölgelerde ortak sabit (adım 50 kararı)
        use_monthly_k, k_used = False, pd.Series(float(cfg["k_n20"]), index=range(1, 13))

    # 3. seri
    d = build_series(region, coef, k_used)
    d.to_parquet(out_dir / "harmonized_daily.parquet", index=False)
    d["ym"] = d.acq_date.str[:7]
    mon = d.groupby("ym").agg(h=("h", "sum"), m=("m", "sum"), v=("v", "sum"), m_day=("m_day", "sum"), m_night=("m_night", "sum"),
                              src=("src", "first")).reset_index()
    months = pd.period_range(region["first_month"], d.acq_date.max()[:7], freq="M").strftime("%Y-%m")
    mon = mon.set_index("ym").reindex(months).reset_index().rename(columns={"index": "ym"})
    mon["src"] = np.where(mon.ym < VIIRS_START[:7], "M", np.where(mon.ym >= N20_START[:7], "N", "V"))
    mon[["h", "m", "v", "m_day", "m_night"]] = mon[["h", "m", "v", "m_day", "m_night"]].fillna(0)
    mon["mo"] = mon.ym.str[5:].astype(int)
    mon["y"] = mon.ym.str[:4].astype(int)
    # belirsizlik aralığı (yalnızca tahmin ayları)
    est = mon.src != "V"
    lo = np.where(mon.src == "M", unc["p16"], n20_stats["monthly_actual_over_predicted_p16_p84"][0])
    hi = np.where(mon.src == "M", unc["p84"], n20_stats["monthly_actual_over_predicted_p16_p84"][1])
    wide = (mon.src == "M") & (mon.m > cal.groupby(["y", "mo"]).m.sum().groupby("mo").max().reindex(mon.mo).to_numpy())
    lo, hi = np.where(wide, unc["p05"], lo), np.where(wide, unc["p95"], hi)   # sınanmış aralık dışı: geniş aralık
    mon["h_lo"] = np.where(est, mon.h * lo, mon.h).round(1)
    mon["h_hi"] = np.where(est, mon.h * hi, mon.h).round(1)
    # sınanmış aralık: kalibrasyon yıllarında o takvim ayında görülen en yüksek MODIS sayısı
    cal_m = cal.groupby(["y", "mo"]).m.sum().groupby("mo").max()
    mon["tested_max_m"] = cal_m.reindex(mon.mo).to_numpy()
    mon["range_ratio"] = (mon.m / mon.tested_max_m).round(2)
    mon["out_of_range"] = (mon.src == "M") & (mon.m > mon.tested_max_m)
    gaps = {"M": gap_days_by_month("MODIS"), "V": gap_days_by_month("SNPP"), "N": gap_days_by_month("NOAA20")}
    mon["gap_days"] = [gaps[s].get(ym, 0) for s, ym in zip(mon.src, mon.ym)]
    mon["h"] = mon.h.round(1)
    mon[["ym", "src", "h", "h_lo", "h_hi", "m", "v", "out_of_range", "range_ratio", "gap_days"]].to_csv(out_dir / "harmonized_monthly.csv", index=False)

    # alt bölge düzeyinde sınanmış aralık dışı (hücre × gün tablosundan)
    from overlap import zone_of
    d["zone"] = zone_of(d.i, d.j, float(region["cell_deg"]))
    zm = d[d.src == "M"].assign(mo=lambda x: x.ym.str[5:].astype(int)).groupby(["ym", "mo", "zone"]).agg(m=("m", "sum"), h=("h", "sum")).reset_index()
    cal_zm = cal.groupby(["y", "mo", "zone"]).m.sum().groupby(["mo", "zone"]).max()
    zm["tested_max_m"] = cal_zm.reindex(pd.MultiIndex.from_frame(zm[["mo", "zone"]])).to_numpy()
    zm["range_ratio"] = (zm.m / zm.tested_max_m).round(2)
    zo = zm[(zm.m > zm.tested_max_m) & (zm.m >= 300)].sort_values("range_ratio", ascending=False)
    if suffix:                                    # alt bölgeler yalnızca Türkiye için tanımlı
        zo = zo.iloc[0:0]

    oor = mon[mon.out_of_range]
    coefficients = {
        "generated": date.today().isoformat(), "region": region["name"],
        "method": method_text,
        "calibration_years": [2012, STABLE_LAST], "calibration_note": "Terra and Aqua overpass times are stable through 2022; 2023-2025 (orbit drift) used only as an independent test",
        "viirs_start": VIIRS_START, "noaa20_start": N20_START,
        "modis_to_snpp": {str(mo): round(float(coef.loc[mo, "all"]), 3) for mo in range(1, 13)},
        "noaa20_to_snpp": {"by_month": use_monthly_k, "k": {str(mo): round(float(k_used.loc[mo]), 3) for mo in range(1, 13)},
                           "k_constant": float(k_used.loc[1]) if not use_monthly_k else n20_stats["k_constant"],
                           "k_region_own": n20_stats["k_constant"], "years": list(N20_YEARS)},
        "uncertainty": {"modis_months_actual_over_estimate_p16_p84": [unc["p16"], unc["p84"]],
                        "noaa20_months_actual_over_estimate_p16_p84": n20_stats["monthly_actual_over_predicted_p16_p84"],
                        "out_of_range_months_p05_p95": [unc["p05"], unc["p95"]],
                        "note": "68% of months in leave-one-year-out testing fall inside the p16-p84 band; months above the tested MODIS range get the wider p05-p95 band and are probably overestimates; not a formal confidence interval"},
        "out_of_tested_range_months": [{"month": r.ym, "modis": int(r.m), "tested_max": int(r.tested_max_m), "times_tested_max": float(r.range_ratio)} for r in oor.itertuples()],
        "out_of_tested_range_zone_months": [{"month": r.ym, "zone": r.zone, "modis": int(r.m), "tested_max": int(r.tested_max_m), "times_tested_max": float(r.range_ratio)} for r in zo.itertuples()],
    }
    if cfg.get("quality"):
        coefficients["quality"] = cfg["quality"]
    for path in (out_dir / "coefficients.json", DOCS / f"coefficients{suffix}.json"):
        path.write_text(json.dumps(coefficients, indent=1, ensure_ascii=False), encoding="utf-8")

    stats = {
        "models_leave_one_year_out": models, "uncertainty": unc, "level_effect": lvl,
        "coef_calibration_2012_2022": {p: {int(mo): round(float(coef.loc[mo, p]), 2) for mo in range(1, 13)} for p in coef.columns},
        "coef_if_all_years_2012_2025": {p: {int(mo): round(float(coef_all_years.loc[mo, p]), 2) for mo in range(1, 13)} for p in coef_all_years.columns},
        "calibration_counts": {int(mo): {"modis_day": int(g.m_day.sum()), "modis_night": int(g.m_night.sum())} for mo, g in cal.groupby("mo")},
        "cv_year_actual_vs_predicted": {int(y): {"viirs": int(r.v), "predicted": int(round(r.pred)), "err_pct": round(float((r.pred - r.v) / r.v * 100), 1)} for y, r in ry.iterrows()},
        "noaa20": n20_stats,
        "effect_of_drift_years_on_2002_2011_total_pct": None,
        "yearly": {int(y): {"h": round(float(g.h.sum())), "m": int(g.m.sum()), "v": int(g.v.sum()), "h_lo": round(float(g.h_lo.sum())), "h_hi": round(float(g.h_hi.sum()))} for y, g in mon.groupby("y")},
        "out_of_range_months": coefficients["out_of_tested_range_months"],
        "out_of_range_zone_months": coefficients["out_of_tested_range_zone_months"][:25],
        "nov_2026": mon[mon.ym == "2026-11"][["h", "h_lo", "h_hi", "m", "v"]].to_dict("records"),
    }
    # katsayı tüm yıllardan (2012–2025) hesaplansaydı 2002–2011 tahmini ne kadar değişirdi
    me = mon[mon.src == "M"]
    alt = (me.m * coef_all_years["all"].reindex(me.mo).to_numpy()).sum()
    stats["effect_of_drift_years_on_2002_2011_total_pct"] = round(float((alt - me.h.sum()) / me.h.sum() * 100), 1)
    const = float(cal.v.sum() / cal.m.sum())
    stats["single_constant_coefficient"] = round(const, 3)
    stats["effect_of_monthly_vs_constant_by_year_pct"] = {int(y): round(float((me.h[me.y == y].sum() - me.m[me.y == y].sum() * const) / (me.m[me.y == y].sum() * const) * 100), 1) for y in sorted(me.y.unique())}
    stats["method"], stats["k_n20_used"] = method, float(k_used.loc[1])
    (DOCS / f"harmonize_stats{suffix}.json").write_text(json.dumps(stats, indent=1, ensure_ascii=False), encoding="utf-8")
    keys = ["models_leave_one_year_out", "uncertainty", "level_effect", "cv_year_actual_vs_predicted", "out_of_range_months", "effect_of_drift_years_on_2002_2011_total_pct"]
    print(json.dumps({k: stats[k] for k in keys}, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
