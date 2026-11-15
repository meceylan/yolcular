# AI-assisted: generated with Claude (Anthropic)
"""Adım 23: veri kontrol raporu.

detections.parquet dosyasından sayım grafikleri, boşluk günleri, 2021 piki ve
MODIS 2009-2011 incelemesini üretir. Grafikler docs/report_*.png, sayılar
docs/data_report_stats.json içine yazılır.
"""
import argparse
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, LogNorm

from common import DATA_PROCESSED, DOCS

C_MODIS, C_VIIRS = "#2a78d6", "#eb6834"
C_REG = {"Güneydoğu": "#2a78d6", "İç Anadolu": "#eb6834", "Çukurova": "#1baf7a",
         "Ege-Akdeniz kıyısı": "#eda100", "Diğer": "#898781"}
INK, MUTED, GRID, GAP = "#0b0b0b", "#898781", "#e1e0d9", "#c3c2b7"
SEQ = LinearSegmentedColormap.from_list("seq", ["#f4f8fd", "#cde2fb", "#86b6ef", "#2a78d6", "#0d366b"])
plt.rcParams.update({"figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "savefig.facecolor": "#fcfcfb",
                     "axes.edgecolor": "#c3c2b7", "axes.labelcolor": "#52514e", "xtick.color": MUTED,
                     "ytick.color": MUTED, "text.color": INK, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
                     "axes.axisbelow": True, "font.size": 9, "axes.titlesize": 10.5, "axes.titleweight": "bold",
                     "axes.titlelocation": "left", "legend.frameon": False, "figure.dpi": 130})

# data_gaps.md: (başlangıç, bitiş, etiket)
MODIS_GAPS = [("2002-07-01", "2002-12-31", "2002: dağınık eksik günler"),
              ("2007-08-15", "2007-12-31", "2007 Ağu ortasından: kısmen eksik"),
              ("2009-04-21", "2009-04-22", "21-22 Nis 2009")]
VIIRS_GAPS = [("2022-07-27", "2022-08-10"), ("2024-05-30", "2024-06-03"), ("2024-07-10", "2024-07-15"),
              ("2024-07-25", "2024-07-28"), ("2024-09-26", "2024-09-26"), ("2025-07-06", "2025-07-07")]


def region(x):
    r = pd.Series("Diğer", index=x.index)
    r[x.latitude.between(36.5, 38.5) & x.longitude.between(38, 42.5)] = "Güneydoğu"
    r[x.latitude.between(38, 40.2) & x.longitude.between(32, 36.5)] = "İç Anadolu"
    r[x.latitude.between(36, 38.6) & x.longitude.between(27, 32.5)] = "Ege-Akdeniz kıyısı"
    r[x.latitude.between(36, 37.6) & x.longitude.between(34.5, 37)] = "Çukurova"
    return r


def zero_runs(dates, start, end, months, min_len):
    """[start, end] içinde, verilen aylarda, tespitsiz ardışık gün dizileri."""
    have = set(pd.to_datetime(pd.Series(dates).unique()))
    runs, cur = [], []
    for day in pd.date_range(start, end):
        if day.month in months and day not in have:
            cur.append(day)
        else:
            if len(cur) >= min_len:
                runs.append([cur[0].strftime("%Y-%m-%d"), cur[-1].strftime("%Y-%m-%d"), len(cur)])
            cur = []
    if len(cur) >= min_len:
        runs.append([cur[0].strftime("%Y-%m-%d"), cur[-1].strftime("%Y-%m-%d"), len(cur)])
    return runs


def shade(ax, gaps, label):
    for n, g in enumerate(gaps):
        a, b = pd.Timestamp(g[0]), pd.Timestamp(g[1]) + pd.Timedelta(days=1)
        if (b - a).days < 20:  # dar boşluk grafikte görünsün
            mid = a + (b - a) / 2
            a, b = mid - pd.Timedelta(days=10), mid + pd.Timedelta(days=10)
        ax.axvspan(a, b, color=GAP, alpha=0.55, lw=0, label=label if n == 0 else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="turkiye")
    reg_id = ap.parse_args().region
    d = pd.read_parquet(DATA_PROCESSED / reg_id / "detections.parquet")
    d["date"] = pd.to_datetime(d.acq_date)
    d["y"], d["mo"] = d.date.dt.year, d.date.dt.month
    d["ym"] = d.date.dt.to_period("M").dt.to_timestamp()
    d["ok"] = ~d.flag_static & ~d.flag_offshore & ~d.flag_low_conf
    k = d[d.in_country].copy()
    k["reg"] = region(k)
    m, v = k[k.sensor == "MODIS"], k[k.satellite == "SNPP"]
    mf, vf = m[m.ok], v[v.ok]
    S = {}

    # ---------- 1. yıllık ----------
    yr = pd.DataFrame({"modis_raw": m.groupby("y").size(), "modis_no_static": m[~m.flag_static & ~m.flag_offshore].groupby("y").size(),
                       "modis_filtered": mf.groupby("y").size(), "viirs_raw": v.groupby("y").size(),
                       "viirs_filtered": vf.groupby("y").size()})
    S["yearly"] = {int(y): {c: (None if pd.isna(x) else int(x)) for c, x in r.items()} for y, r in yr.iterrows()}
    fig, axes = plt.subplots(2, 1, figsize=(10, 6.2), sharex=True)
    for ax, raw, flt, col, name in [(axes[0], "modis_raw", "modis_filtered", C_MODIS, "MODIS (Terra + Aqua)"),
                                    (axes[1], "viirs_raw", "viirs_filtered", C_VIIRS, "VIIRS S-NPP")]:
        ax.bar(yr.index, yr[raw], width=0.8, color=col, alpha=0.3, label="Ham (sınır içi)")
        ax.bar(yr.index, yr[flt], width=0.5, color=col, label="Sabit kaynak, deniz ve düşük güven çıkarılmış")
        ax.set_title(f"{name}: yıllık tespit sayısı")
        ax.grid(axis="x", visible=False)
        ax.legend(loc="upper left", ncol=2)
        ax.set_ylim(0, yr[raw].max() * 1.25)
    axes[0].annotate("2002: Tem–Ara", (2002, yr.modis_raw[2002]), ha="center", va="bottom", fontsize=7.5, color=MUTED)
    for ax, c in [(axes[0], "modis_raw"), (axes[1], "viirs_raw")]:
        ax.annotate("2026: 13 Kas'a kadar", (2026, yr[c][2026]), ha="center", va="bottom", fontsize=7.5, color=MUTED)
    axes[1].set_xticks(range(2002, 2027, 2))
    fig.tight_layout()
    fig.savefig(DOCS / "report_yearly.png")
    plt.close(fig)

    # ---------- 2. aylık + boşluklar ----------
    idx = pd.date_range("2002-07-01", "2026-11-01", freq="MS")
    mm_raw = m.groupby("ym").size().reindex(idx, fill_value=0)
    mm = mf.groupby("ym").size().reindex(idx, fill_value=0)
    vidx = pd.date_range("2012-01-01", "2026-10-01", freq="MS")
    vm_raw = v.groupby("ym").size().reindex(vidx, fill_value=0)
    vm = vf.groupby("ym").size().reindex(vidx, fill_value=0)
    fig, axes = plt.subplots(2, 1, figsize=(11, 6.4), sharex=True)
    axes[0].plot(idx, mm_raw, color=C_MODIS, lw=1, alpha=0.4, label="Ham")
    axes[0].plot(idx, mm, color=C_MODIS, lw=1.6, label="Filtreli")
    shade(axes[0], MODIS_GAPS, "Eksik veri dönemi (NASA uyarısı)")
    axes[0].set_title("MODIS: aylık tespit sayısı")
    axes[1].plot(vidx, vm_raw, color=C_VIIRS, lw=1, alpha=0.4, label="Ham")
    axes[1].plot(vidx, vm, color=C_VIIRS, lw=1.6, label="Filtreli")
    shade(axes[1], VIIRS_GAPS, "VIIRS kesintisi (tespitsiz yaz günleri)")
    axes[1].set_title("VIIRS S-NPP: aylık tespit sayısı")
    for ax in axes:
        ax.legend(loc="upper left", ncol=3)
        ax.set_ylim(0, ax.get_ylim()[1] * 1.15)
    fig.tight_layout()
    fig.savefig(DOCS / "report_monthly.png")
    plt.close(fig)

    # ---------- 3. takvim (yıl x ay) ----------
    fig, axes = plt.subplots(1, 2, figsize=(11, 6.2))
    for ax, x, name in [(axes[0], mf, "MODIS (filtreli)"), (axes[1], vf, "VIIRS S-NPP (filtreli)")]:
        t = x.groupby(["y", "mo"]).size().unstack().reindex(columns=range(1, 13))
        im = ax.imshow(t.values, aspect="auto", cmap=SEQ, norm=LogNorm(vmin=10, vmax=np.nanmax(t.values)))
        ax.set_yticks(range(len(t.index)), t.index)
        ax.set_xticks(range(12), ["O", "Ş", "M", "N", "M", "H", "T", "A", "E", "E", "K", "A"])
        ax.grid(False)
        ax.set_title(f"{name}: yıl × ay")
        fig.colorbar(im, ax=ax, shrink=0.7, label="Tespit sayısı (log)")
    fig.tight_layout()
    fig.savefig(DOCS / "report_calendar.png")
    plt.close(fig)

    # ---------- 4. boşluk günleri ----------
    allm, allv = d[d.sensor == "MODIS"], d[d.satellite == "SNPP"]
    summer = {6, 7, 8, 9}
    S["gaps"] = {
        "modis_2002_zero_days_jul_oct": zero_runs(allm.date, "2002-07-01", "2002-10-31", {7, 8, 9, 10}, 1),
        "modis_2007_zero_days_aug15_oct": zero_runs(allm.date, "2007-08-15", "2007-10-31", {8, 9, 10}, 1),
        "modis_2009_04_21_22_rows": int(allm.acq_date.astype(str).isin(["2009-04-21", "2009-04-22"]).sum()),
        "modis_summer_zero_runs_ge2": zero_runs(allm.date, "2002-07-01", "2026-10-31", summer, 2),
        "terra_summer_zero_runs_ge3": zero_runs(allm[allm.satellite == "Terra"].date, "2002-07-01", "2026-10-31", summer, 3),
        "aqua_summer_zero_runs_ge3": zero_runs(allm[allm.satellite == "Aqua"].date, "2002-07-04", "2026-10-31", summer, 3),
        "viirs_summer_zero_runs_ge1": zero_runs(allv.date, "2012-02-01", "2026-10-31", summer | {5}, 1),
        "modis_zero_days_per_year": {int(y): int(n) for y, n in (
            pd.Series(1, index=pd.date_range("2002-07-01", "2026-11-13").difference(pd.DatetimeIndex(allm.date.unique())))
            .groupby(lambda t: t.year).sum()).items()},
    }
    # MODIS'in düşük kaldığı yaz ayları: aynı ayın VIIRS/MODIS oranına göre
    S["modis_aug_2022"] = {"modis_filtered": int(mm[pd.Timestamp("2022-08-01")]), "viirs_filtered": int(vm[pd.Timestamp("2022-08-01")]),
                           "modis_days_with_data": int(m[(m.y == 2022) & (m.mo == 8)].acq_date.nunique())}

    # ---------- 5. 2021 piki ----------
    eg_m, eg_v = mf[mf.reg == "Ege-Akdeniz kıyısı"], vf[vf.reg == "Ege-Akdeniz kıyısı"]
    ja_m = eg_m[eg_m.mo.isin([7, 8])].groupby("y").size()
    ja_v = eg_v[eg_v.mo.isin([7, 8])].groupby("y").size()
    frp_m = eg_m[eg_m.mo.isin([7, 8])].groupby("y").frp.sum()
    days = pd.date_range("2021-07-15", "2021-08-31")
    dm = eg_m[eg_m.y == 2021].groupby("date").size().reindex(days, fill_value=0)
    dv = eg_v[eg_v.y == 2021].groupby("date").size().reindex(days, fill_value=0)
    S["peak_2021"] = {
        "modis_jul_aug_2021": int(ja_m[2021]), "modis_jul_aug_median_other_years": float(ja_m.drop([2021, 2002, 2026]).median()),
        "modis_rank_2021": int(ja_m.rank(ascending=False)[2021]),
        "viirs_jul_aug_2021": int(ja_v[2021]), "viirs_jul_aug_median_other_years": float(ja_v.drop([2021, 2026]).median()),
        "viirs_rank_2021": int(ja_v.rank(ascending=False)[2021]),
        "modis_frp_2021_MW": float(frp_m[2021]), "modis_frp_median_other_MW": float(frp_m.drop([2021, 2002, 2026]).median()),
        "modis_peak_day": [dm.idxmax().strftime("%Y-%m-%d"), int(dm.max())],
        "viirs_peak_day": [dv.idxmax().strftime("%Y-%m-%d"), int(dv.max())],
        "modis_28jul_12aug": int(dm["2021-07-28":"2021-08-12"].sum()), "viirs_28jul_12aug": int(dv["2021-07-28":"2021-08-12"].sum()),
    }
    fig, axes = plt.subplots(2, 2, figsize=(11, 6.2), gridspec_kw={"width_ratios": [1.25, 1]})
    for row, (ja, dd, col, name) in enumerate([(ja_m, dm, C_MODIS, "MODIS"), (ja_v, dv, C_VIIRS, "VIIRS S-NPP")]):
        ax = axes[row, 0]
        ax.bar(ja.index, ja.values, width=0.7, color=[col if y == 2021 else col + "55" for y in ja.index])
        ax.annotate("2021", (2021, ja[2021]), ha="center", va="bottom", fontsize=8.5, fontweight="bold")
        ax.set_title(f"{name}: Ege-Akdeniz kıyısı, Temmuz–Ağustos toplamı (filtreli)")
        ax.grid(axis="x", visible=False)
        ax.set_ylim(0, ja.max() * 1.15)
        ax = axes[row, 1]
        ax.bar(dd.index, dd.values, width=0.8, color=col)
        ax.set_title(f"{name}: günlük, 15 Tem – 31 Ağu 2021")
        ax.grid(axis="x", visible=False)
        ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(DOCS / "report_peak2021.png")
    plt.close(fig)

    # ---------- 6. MODIS 2009-2011 ----------
    yrs_m = list(range(2003, 2026))
    full = m[m.y.between(2003, 2025)]
    hi, post = [2009, 2010, 2011], list(range(2012, 2026))

    def per_year(x):
        return x.groupby("y").size().reindex(yrs_m, fill_value=0)
    variants = {"ham": full, "sabit kaynak ve deniz çıkarılmış": full[~full.flag_static & ~full.flag_offshore],
                "düşük güven de çıkarılmış": full[full.ok], "yalnızca yüksek güven": full[full.ok & (full.confidence_class == "high")],
                "yalnızca gündüz (filtreli)": full[full.ok & (full.daynight == "D")]}
    S["excess_filters"] = {}
    for name, x in variants.items():
        p = per_year(x)
        S["excess_filters"][name] = {"mean_2009_2011": round(float(p[hi].mean()), 0), "mean_2012_2025": round(float(p[post].mean()), 0),
                                     "max_2012_2025": int(p[post].max()), "ratio": round(float(p[hi].mean() / p[post].mean()), 2)}
    removed = 1 - per_year(full[full.ok]) / per_year(full)
    S["filter_removed_share"] = {"2009_2011": round(float(removed[hi].mean()), 3), "2012_2025": round(float(removed[post].mean()), 3)}

    ao = mf[mf.mo.between(8, 10) & mf.y.between(2003, 2025)]
    by_reg = ao.groupby(["y", "reg"]).size().unstack().reindex(yrs_m).fillna(0)[list(C_REG)]
    rest = mf[~mf.mo.between(8, 10) & mf.y.between(2003, 2025)].groupby("y").size()
    S["aug_oct_by_region"] = {int(y): {c: int(x) for c, x in r.items()} for y, r in by_reg.iterrows()}
    S["rest_of_year_filtered"] = {"mean_2009_2011": float(rest[hi].mean()), "mean_2012_2025": float(rest[post].mean())}
    S["excess_region"] = {c: {"mean_2009_2011": round(float(by_reg.loc[hi, c].mean())), "mean_2012_2025": round(float(by_reg.loc[post, c].mean())),
                              "max_2012_2025": int(by_reg.loc[post, c].max()), "max_year": int(by_reg.loc[post, c].idxmax())} for c in by_reg}

    vao = vf[vf.mo.between(8, 10) & vf.y.between(2012, 2025)].groupby(["y", "reg"]).size().unstack().fillna(0)[list(C_REG)]
    ratio = vao / by_reg.loc[2012:2025]
    S["viirs_modis_ratio_aug_oct"] = {c: {"ratio_of_sums": round(float(vao[c].sum() / by_reg.loc[2012:2025, c].sum()), 2),
                                           "mean_of_yearly_ratios": round(float(ratio[c].mean()), 2),
                                           "min": round(float(ratio[c].min()), 2), "max": round(float(ratio[c].max()), 2)} for c in vao}
    ann_ratio = (vf.groupby("y").size() / mf.groupby("y").size()).loc[2012:2025]
    S["viirs_modis_ratio_annual"] = {int(y): round(float(x), 2) for y, x in ann_ratio.items()}

    # nitelikler: 2009-2011 ile VIIRS dönemindeki yoğun yıllar (2013, 2015, 2016)
    core = ao[ao.reg.isin(["Güneydoğu", "İç Anadolu"])]
    def traits(x):
        return {"n": int(len(x)), "frp_median": round(float(x.frp.median()), 1), "night_pct": round(float((x.daynight == "N").mean() * 100), 1),
                "terra_pct": round(float((x.satellite == "Terra").mean() * 100), 1),
                "high_conf_pct": round(float((x.confidence_class == "high").mean() * 100), 1), "scan_mean": round(float(x.scan.mean()), 2),
                "days_with_fire_per_year": round(float(x.groupby("y").acq_date.nunique().mean()), 0)}
    S["traits_gd_ia_aug_oct"] = {"2009_2011": traits(core[core.y.isin(hi)]), "2013_2015_2016": traits(core[core.y.isin([2013, 2015, 2016])]),
                                 "2003_2008": traits(core[core.y.between(2003, 2008)]), "other_2012_2025": traits(core[core.y.isin(post) & ~core.y.isin([2013, 2015, 2016])])}

    def cells(x):
        return x.groupby([np.floor(x.latitude / 0.25), np.floor(x.longitude / 0.25)]).size()
    A = cells(ao[ao.y.isin(hi)])
    B = cells(ao[ao.y.isin([2013, 2015, 2016])])
    vv = vf[vf.mo.between(8, 10)]
    Cc = cells(vv[vv.y.isin([2013, 2015, 2016])])
    X = pd.concat([A, B, Cc], axis=1).fillna(0)
    X.columns = ["m0911", "m131516", "v131516"]
    S["cell_correlation"] = {"modis0911_vs_modis131516": round(float(X.m0911.corr(X.m131516)), 2),
                             "modis0911_vs_viirs131516": round(float(X.m0911.corr(X.v131516)), 2),
                             "modis131516_vs_viirs131516": round(float(X.m131516.corr(X.v131516)), 2)}
    S["duplicates_modis"] = int(d[d.sensor == "MODIS"].duplicated(["satellite", "acq_date", "latitude", "longitude"]).sum())

    # şekil: bölgelere göre Ağu-Eki
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    bottom = np.zeros(len(by_reg))
    for c in by_reg:
        ax.bar(by_reg.index, by_reg[c], bottom=bottom, width=0.72, color=C_REG[c], label=c, edgecolor="#fcfcfb", linewidth=0.8)
        bottom += by_reg[c].values
    ax.axvspan(2008.5, 2011.5, color=GAP, alpha=0.3, lw=0)
    ax.axvline(2011.5, color=MUTED, lw=1, ls="--")
    ax.text(2011.6, bottom.max() * 1.02, "VIIRS dönemi →", fontsize=8, color=MUTED, va="bottom")
    ax.set_title("MODIS: Ağustos–Ekim tespitleri, bölgelere göre (filtreli)")
    ax.set_xticks(yrs_m)
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="x", visible=False)
    ax.set_ylim(0, bottom.max() * 1.12)
    ax.legend(loc="upper left", ncol=5, fontsize=8)
    fig.tight_layout()
    fig.savefig(DOCS / "report_modis_2009_2011_regions.png")
    plt.close(fig)

    # şekil: haritalar
    fig, axes = plt.subplots(3, 1, figsize=(7.5, 9.6), sharex=True, sharey=True)
    for ax, x, name, n in [(axes[0], ao[ao.y.isin(hi)], "MODIS 2009–2011", 3), (axes[1], ao[ao.y.isin([2013, 2015, 2016])], "MODIS 2013, 2015, 2016", 3),
                           (axes[2], vv[vv.y.isin([2013, 2015, 2016])], "VIIRS 2013, 2015, 2016", 3)]:
        c = cells(x) / n
        la, lo = c.index.get_level_values(0) * 0.25 + 0.125, c.index.get_level_values(1) * 0.25 + 0.125
        sc = ax.scatter(lo, la, c=c.values, s=13, marker="s", cmap=SEQ, norm=LogNorm(vmin=1, vmax=c.max()), linewidths=0)
        ax.set_title(f"{name}: Ağu–Eki, hücre başına yıllık ortalama tespit")
        ax.set_aspect(1.28)
        ax.set_xlim(25.6, 44.9)
        ax.set_ylim(35.8, 42.2)
        fig.colorbar(sc, ax=ax, shrink=0.85)
    fig.tight_layout()
    fig.savefig(DOCS / "report_modis_2009_2011_maps.png")
    plt.close(fig)

    # şekil: VIIRS/MODIS oranı etkinlik düzeyine göre
    fig, ax = plt.subplots(figsize=(7, 4.6))
    for c in ["Güneydoğu", "İç Anadolu", "Çukurova", "Ege-Akdeniz kıyısı", "Diğer"]:
        ax.scatter(by_reg.loc[2012:2025, c], ratio[c], s=34, color=C_REG[c], label=c, edgecolors="#fcfcfb", linewidths=0.8)
    for c, yy in [("İç Anadolu", 2009), ("İç Anadolu", 2011), ("Güneydoğu", 2009)]:
        ax.axvline(by_reg.loc[yy, c], color=C_REG[c], lw=1, ls=":")
        ax.text(by_reg.loc[yy, c], 7.3, f"{c} {yy} ", fontsize=7.5, color="#52514e", rotation=90, va="top", ha="right")
    ax.set_xscale("log")
    ax.set_xlabel("MODIS Ağu–Eki tespit sayısı (bölge, yıl)")
    ax.set_ylabel("VIIRS / MODIS oranı")
    ax.set_title("Oran etkinlik düzeyine bağlı: az yangında oran yüksek")
    ax.legend(fontsize=8, loc="lower left")
    fig.tight_layout()
    fig.savefig(DOCS / "report_ratio_vs_level.png")
    plt.close(fig)

    (DOCS / "data_report_stats.json").write_text(json.dumps(S, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k2: S[k2] for k2 in S if k2 not in ("yearly", "aug_oct_by_region")}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
