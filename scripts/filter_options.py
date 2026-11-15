# AI-assisted: generated with Claude (Anthropic)
"""Adım 28: filtre seçeneklerini dener.

- Gevşek / orta / sıkı filtrede kalan tespit sayısı ve VIIRS/MODIS oranı
- Arşivdeki sabit kaynak konumlarından maske (NRT verisi için) ve sınaması
- Kasım 2026 oranı, Ağustos 2022 ve Aralık 2018 kontrolü
Çıktı: docs/filter_stats.json, docs/filter_ratio_by_year.png
"""
import argparse
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import DATA_PROCESSED, DOCS

CELL = 0.01  # maske hücresi, derece (~1 km)
COL = {"Gevşek": "#2a78d6", "Orta": "#eb6834", "Sıkı": "#1baf7a"}


def cell_ids(lat, lon):
    return (np.floor(lat / CELL).astype(np.int64) * 100000 + np.floor((lon + 180) / CELL).astype(np.int64))


def neighbours(ids, r):
    out = set()
    for di in range(-r, r + 1):
        for dj in range(-r, r + 1):
            out.update((ids + di * 100000 + dj).tolist())
    return out


def build_mask(src, min_days):
    """type 2/3 tespitlerinin en az min_days ayrı günde görüldüğü hücreler."""
    s = src[src.type.isin([2, 3])]
    days = s.groupby("cell").acq_date.nunique()
    return days[days >= min_days].index.to_numpy()


def in_mask(x, mask_cells, r_viirs, r_modis):
    mv, mm = neighbours(mask_cells, r_viirs), neighbours(mask_cells, r_modis)
    return np.where(x.sensor == "VIIRS", x.cell.isin(mv), x.cell.isin(mm))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="turkiye")
    reg = ap.parse_args().region
    d = pd.read_parquet(DATA_PROCESSED / reg / "detections.parquet")
    d["date"] = pd.to_datetime(d.acq_date)
    d["y"], d["mo"] = d.date.dt.year, d.date.dt.month
    d["conf"] = pd.to_numeric(d.confidence_raw, errors="coerce")
    d["cell"] = cell_ids(d.latitude.to_numpy(), d.longitude.to_numpy())
    k = d[d.in_country]
    S = {}

    # ---------- güven dağılımı ----------
    sp = k[~k.is_nrt & k.y.between(2012, 2025)]
    mo_, vi_ = sp[sp.sensor == "MODIS"], sp[sp.satellite == "SNPP"]
    fire_m, fire_v = mo_[mo_.type == 0], vi_[vi_.type == 0]
    S["confidence"] = {
        "modis_type0_share": {"lt30": round(float((fire_m.conf < 30).mean() * 100), 1),
                              "30_79": round(float(fire_m.conf.between(30, 79).mean() * 100), 1),
                              "ge80": round(float((fire_m.conf >= 80).mean() * 100), 1)},
        "viirs_type0_share": {c: round(float((fire_v.confidence_class == c).mean() * 100), 1) for c in ["low", "nominal", "high"]},
        "modis_static_share_by_class": {c: round(float((mo_[mo_.confidence_class == c].type.isin([1, 2, 3])).mean() * 100), 1) for c in ["low", "nominal", "high"]},
        "viirs_static_share_by_class": {c: round(float((vi_[vi_.confidence_class == c].type.isin([1, 2, 3])).mean() * 100), 1) for c in ["low", "nominal", "high"]},
        "viirs_low_day_share": round(float((fire_v[fire_v.confidence_class == "low"].daynight == "D").mean() * 100), 1),
        "modis_low_day_share": round(float((fire_m[fire_m.confidence_class == "low"].daynight == "D").mean() * 100), 1),
    }

    # ---------- seçenekler (2012-2025, SP) ----------
    notstatic = ~sp.type.isin([1, 2, 3])
    opts = {
        "Ham": pd.Series(True, index=sp.index),
        "Gevşek": notstatic,
        "Orta": notstatic & (sp.confidence_class != "low"),
        "Sıkı": notstatic & (sp.confidence_class == "high"),
    }
    S["options"] = {}
    ratio_year = {}
    for name, keep in opts.items():
        x = sp[keep]
        m, v = x[x.sensor == "MODIS"], x[x.satellite == "SNPP"]
        ym, yv = m.groupby("y").size(), v.groupby("y").size()
        r = yv / ym
        ratio_year[name] = r
        mm = m.groupby(["y", "mo"]).size()
        vm = v.groupby(["y", "mo"]).size()
        j = pd.concat([mm, vm], axis=1).fillna(0)
        j.columns = ["m", "v"]
        mr = (j.v / j.m)[j.m >= 100]
        S["options"][name] = {
            "modis_kept": int(len(m)), "modis_kept_pct": round(len(m) / len(mo_) * 100, 1),
            "viirs_kept": int(len(v)), "viirs_kept_pct": round(len(v) / len(vi_) * 100, 1),
            "ratio_of_sums": round(len(v) / len(m), 2),
            "ratio_year_min": round(float(r.min()), 2), "ratio_year_max": round(float(r.max()), 2),
            "ratio_year_cv_pct": round(float(r.std() / r.mean() * 100), 1),
            "ratio_month_cv_pct": round(float(mr.std() / mr.mean() * 100), 1),
            "monthly_corr": round(float(j.m.corr(j.v)), 3),
            "modis_min_month": int(j.m.min()), "modis_months_lt50": int((j.m < 50).sum()),
        }
    # MODIS eşiği değişirse (VIIRS n+h sabit): oran kararlılığı
    S["modis_threshold_scan"] = {}
    v_mid = sp[notstatic & (sp.satellite == "SNPP") & (sp.confidence_class != "low")].groupby("y").size()
    for thr in [0, 20, 30, 40, 50]:
        m_thr = sp[notstatic & (sp.sensor == "MODIS") & (sp.conf >= thr)].groupby("y").size()
        r = v_mid / m_thr
        S["modis_threshold_scan"][thr] = {"modis_kept": int(m_thr.sum()), "ratio": round(float(v_mid.sum() / m_thr.sum()), 2),
                                           "cv_pct": round(float(r.std() / r.mean() * 100), 1)}

    fig, ax = plt.subplots(figsize=(9, 4.4))
    plt.rcParams.update({"font.size": 9})
    for name in ["Gevşek", "Orta", "Sıkı"]:
        r = ratio_year[name]
        ax.plot(r.index, r.values, color=COL[name], lw=2, marker="o", ms=5, label=name)
        ax.text(r.index[-1] + 0.15, r.values[-1], name, color="#52514e", va="center", fontsize=8.5)
    ax.set_facecolor("#fcfcfb")
    fig.set_facecolor("#fcfcfb")
    for s_ in ["top", "right"]:
        ax.spines[s_].set_visible(False)
    ax.grid(color="#e1e0d9", lw=0.6)
    ax.set_axisbelow(True)
    ax.set_xlim(2011.5, 2026.3)
    ax.set_ylim(0)
    ax.set_xticks(range(2012, 2026))
    ax.set_ylabel("VIIRS / MODIS (yıllık)")
    ax.set_title("Filtre seçeneğine göre yıllık VIIRS/MODIS oranı", loc="left", fontweight="bold")
    ax.legend(frameon=False, ncol=3, loc="lower left")
    fig.tight_layout()
    fig.savefig(DOCS / "filter_ratio_by_year.png", dpi=130)
    plt.close(fig)

    # ---------- sabit kaynak maskesi ----------
    arch = d[~d.is_nrt & d.type.notna()]  # tüm SP satırları (kutu dahil)
    S["mask_test"] = {}
    train, test = arch[arch.y <= 2024], k[~k.is_nrt & (k.y == 2025) & k.type.notna()]
    test26 = k[~k.is_nrt & (k.y == 2026) & k.type.notna()]
    for min_days in [1, 2, 3, 5]:
        for rv, rm in [(0, 1), (1, 1), (1, 2)]:
            cells = build_mask(train, min_days)
            row = {"mask_cells": int(len(cells))}
            for label, t in [("2025", test), ("2026_jan_jul", test26)]:
                hit = in_mask(t, cells, rv, rm)
                for sens in ["MODIS", "VIIRS"]:
                    ts = t.sensor == sens
                    st = t.type.isin([2, 3])
                    row[f"{label}_{sens}_static_caught_pct"] = round(float(hit[ts & st].mean() * 100), 1)
                    row[f"{label}_{sens}_fire_lost_pct"] = round(float(hit[ts & ~st].mean() * 100), 1)
            S["mask_test"][f"min_days={min_days}, r_viirs={rv}, r_modis={rm}"] = row

    # seçilen maske: tüm arşiv (2026-07'ye kadar), min 3 gün, VIIRS kendi hücresi, MODIS 1 komşu hücre
    MIN_DAYS, RV, RM = 3, 0, 1
    cells = build_mask(arch, MIN_DAYS)
    S["mask_final"] = {"min_days": MIN_DAYS, "r_viirs_cells": RV, "r_modis_cells": RM, "cell_deg": CELL, "mask_cells": int(len(cells))}
    k = k.assign(masked=in_mask(k, cells, RV, RM))
    # maske ile type alanı aynı sonucu veriyor mu (aylık sayılar, 2023-2025)
    chk = k[~k.is_nrt & k.y.between(2023, 2025)]
    for sens, sel in [("MODIS", chk.sensor == "MODIS"), ("SNPP", chk.satellite == "SNPP"), ("NOAA20", chk.satellite == "NOAA20")]:
        a = chk[sel & ~chk.type.isin([1, 2, 3])].groupby(["y", "mo"]).size()
        b = chk[sel & ~chk.masked].groupby(["y", "mo"]).size()
        S["mask_final"][f"{sens}_monthly_mask_vs_type_ratio"] = round(float(b.sum() / a.sum()), 3)
        S["mask_final"][f"{sens}_monthly_corr"] = round(float(a.corr(b)), 4)

    # ---------- 2026 son ayları ve Kasım ----------
    nrt = k[k.is_nrt & k.in_series]
    rows = {}
    for per, x in nrt.groupby(nrt.date.dt.to_period("M")):
        m, v = x[x.sensor == "MODIS"], x[x.sensor == "VIIRS"]
        ok_m = m[~m.masked & (m.confidence_class != "low")]
        ok_v = v[~v.masked & (v.confidence_class != "low")]
        rows[str(per)] = {"modis_raw": int(len(m)), "viirs_raw": int(len(v)), "ratio_raw": round(len(v) / max(len(m), 1), 2),
                          "modis_masked_pct": round(float(m.masked.mean() * 100), 1), "viirs_masked_pct": round(float(v.masked.mean() * 100), 1),
                          "modis_orta": int(len(ok_m)), "viirs_orta": int(len(ok_v)), "ratio_orta": round(len(ok_v) / max(len(ok_m), 1), 2),
                          "viirs_satellite": "/".join(sorted(v.satellite.unique()))}
    S["nrt_months"] = rows
    # Kasım 1-13, önceki yıllar (type ile, orta filtre) : oran bağlamı
    ctx = {}
    for y in range(2012, 2026):
        x = k[(k.y == y) & (k.mo == 11) & (k.date.dt.day <= 13) & ~k.type.isin([1, 2, 3]) & (k.confidence_class != "low")]
        m, v = int((x.sensor == "MODIS").sum()), int((x.satellite == "SNPP").sum())
        ctx[y] = {"modis": m, "viirs_snpp": v, "ratio": round(v / max(m, 1), 2)}
        if y >= 2023:
            n20 = int((x.satellite == "NOAA20").sum())
            ctx[y]["viirs_noaa20"] = n20
    S["november_1_13_context"] = ctx
    nov = nrt[(nrt.date >= "2026-11-01") & (nrt.date <= "2026-11-13")]
    m, v = nov[nov.sensor == "MODIS"], nov[nov.sensor == "VIIRS"]
    S["november_2026_1_13"] = {
        "modis_raw": int(len(m)), "viirs_raw": int(len(v)),
        "modis_after_mask": int((~m.masked).sum()), "viirs_after_mask": int((~v.masked).sum()),
        "modis_orta": int((~m.masked & (m.confidence_class != "low")).sum()),
        "viirs_orta": int((~v.masked & (v.confidence_class != "low")).sum()),
        "modis_days": int(m.acq_date.nunique()), "viirs_days": int(v.acq_date.nunique()),
        "modis_by_sat": {s_: int(n) for s_, n in m.satellite.value_counts().items()},
        "viirs_night_pct_after": round(float((v[~v.masked].daynight == "N").mean() * 100), 1),
    }

    # aylara göre olağan oran (orta filtre, 2012-2025) ve MODIS geçiş saatleri
    mid = k[~k.is_nrt & k.y.between(2012, 2025) & ~k.type.isin([1, 2, 3]) & (k.confidence_class != "low")]
    S["typical_ratio_by_month"] = {}
    for mo_i in [9, 10, 11]:
        g = mid[mid.mo == mo_i]
        r = g[g.satellite == "SNPP"].groupby("y").size() / g[g.sensor == "MODIS"].groupby("y").size()
        S["typical_ratio_by_month"][mo_i] = {"min": round(float(r.min()), 2), "median": round(float(r.median()), 2), "max": round(float(r.max()), 2)}
    dm_ = k[(k.sensor == "MODIS") & (k.daynight == "D") & k.mo.between(9, 11)].copy()
    dm_["hour"] = dm_.acq_time.str[:2].astype(int) + dm_.acq_time.str[2:].astype(int) / 60
    S["modis_day_pass_utc_sep_nov"] = {sat: {int(y): round(float(h), 1) for y, h in dm_[dm_.satellite == sat].groupby("y").hour.median().items() if y in (2005, 2012, 2018, 2021, 2023, 2024, 2025, 2026)} for sat in ["Terra", "Aqua"]}
    S["terra_share_sep_nov"] = {int(y): round(float(v_), 2) for y, v_ in k[(k.sensor == "MODIS") & k.mo.between(9, 11)].groupby("y").apply(lambda g: (g.satellite == "Terra").mean()).items() if y >= 2018}
    n20 = mid[(mid.mo == 11) & (mid.y >= 2023)]
    S["noaa20_over_snpp_november"] = {int(y): round(float((g.satellite == "NOAA20").sum() / (g.satellite == "SNPP").sum()), 2) for y, g in n20.groupby("y")}

    # ---------- Ağustos 2022 ve Aralık 2018 ----------
    def month_check(y, mo):
        x = k[(k.y == y) & (k.mo == mo)]
        f = x[~x.type.isin([1, 2, 3]) & (x.confidence_class != "low")]
        ndays = pd.Period(f"{y}-{mo:02d}").days_in_month
        out = {"days_in_month": ndays}
        for name, sel_all, sel_f in [("modis", x.sensor == "MODIS", f.sensor == "MODIS"), ("terra", x.satellite == "Terra", f.satellite == "Terra"),
                                     ("aqua", x.satellite == "Aqua", f.satellite == "Aqua"), ("viirs", x.satellite == "SNPP", f.satellite == "SNPP")]:
            out[name] = {"raw": int(sel_all.sum()), "filtered": int(sel_f.sum()), "days_with_any_detection": int(x[sel_all].acq_date.nunique())}
        same = k[(k.mo == mo) & k.y.between(2012, 2025) & (k.y != y) & ~k.type.isin([1, 2, 3]) & (k.confidence_class != "low")]
        out["other_years_median"] = {"modis": float(same[same.sensor == "MODIS"].groupby("y").size().median()),
                                     "viirs": float(same[same.satellite == "SNPP"].groupby("y").size().median())}
        return out, x, f
    a22, x22, f22 = month_check(2022, 8)
    mday = f22[f22.sensor == "MODIS"].groupby(f22.date.dt.day).size().reindex(range(1, 32), fill_value=0)
    vday = f22[f22.satellite == "SNPP"].groupby(f22.date.dt.day).size().reindex(range(1, 32), fill_value=0)
    a22["modis_days_1_10"], a22["modis_days_11_31"] = int(mday[1:10].sum()), int(mday[11:31].sum())
    a22["viirs_days_1_10"], a22["viirs_days_11_31"] = int(vday[1:10].sum()), int(vday[11:31].sum())
    r_obs = vday[11:31].sum() / max(mday[11:31].sum(), 1)
    a22["viirs_estimate_if_no_gap"] = int(round(vday[11:31].sum() + r_obs * mday[1:10].sum()))
    j22 = k[(k.y == 2022) & (k.mo == 7) & ~k.type.isin([1, 2, 3]) & (k.confidence_class != "low")]
    a22["july_2022"] = {"modis_27_31": int(((j22.sensor == "MODIS") & (j22.date.dt.day >= 27)).sum()),
                        "modis_1_26": int(((j22.sensor == "MODIS") & (j22.date.dt.day < 27)).sum()),
                        "viirs_1_26": int(((j22.satellite == "SNPP") & (j22.date.dt.day < 27)).sum())}
    S["august_2022"] = a22
    a18, x18, f18 = month_check(2018, 12)
    dec = k[(k.mo == 12) & k.y.between(2012, 2025) & ~k.type.isin([1, 2, 3]) & (k.confidence_class != "low")]
    a18["december_by_year"] = {int(y): {"modis": int((g.sensor == "MODIS").sum()), "viirs": int((g.satellite == "SNPP").sum())} for y, g in dec.groupby("y")}
    st18 = x18[x18.type.isin([2, 3])]
    a18["static_days"] = {"modis": int(st18[st18.sensor == "MODIS"].acq_date.nunique()), "viirs": int(st18[st18.satellite == "SNPP"].acq_date.nunique())}
    a18["static_count"] = {"modis": int((st18.sensor == "MODIS").sum()), "viirs": int((st18.satellite == "SNPP").sum())}
    S["december_2018"] = a18

    # ---------- boşluktan etkilenen aylar (seri kaynağı için eksik gün) ----------
    gaps = {"VIIRS": [("2022-07-27", "2022-08-10"), ("2024-05-30", "2024-06-03"), ("2024-07-10", "2024-07-15"), ("2024-07-25", "2024-07-28"),
                      ("2024-09-26", "2024-09-26"), ("2025-07-06", "2025-07-07"), ("2026-06-01", "2026-06-02"), ("2026-07-11", "2026-07-16")],
            "Aqua": [("2002-07-30", "2002-08-07"), ("2020-08-30", "2020-09-02")],
            "MODIS": [("2014-09-28", "2014-09-29")]}
    gm = {}
    for src, lst in gaps.items():
        for a, b in lst:
            for day in pd.date_range(a, b):
                gm.setdefault(src, {}).setdefault(day.strftime("%Y-%m"), 0)
                gm[src][day.strftime("%Y-%m")] += 1
    S["gap_days_by_month"] = gm

    (DOCS / "filter_stats.json").write_text(json.dumps(S, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(S, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
